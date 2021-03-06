import json
import random
from http.client import HTTPResponse
from typing import Union
from urllib.parse import parse_qsl

import apiai
from chatbase import MessageSet, base_message, MessageTypes
from linebot.models import ImageMessage, TemplateSendMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

from bg_record.manager import BGRecordManager
from chat.manager import ChatManager
from consult_food.manager import ConsultFoodManager
from consult_food.models import SynonymModel
from debby import settings, utils
from drug_ask.manager import DrugAskManager
from food_record.manager import FoodRecordManager
from line.callback import FoodRecordCallback, Callback, BGRecordCallback, ChatCallback, ConsultFoodCallback, \
    DrugAskCallback, ReminderCallback, MyDiaryCallback, UserSettingsCallback, LineCallback
from line.constant import App, BGRecordAction, FoodRecordAction, MyDiaryAction, ConsultFoodAction
from line.manager import LineManager
from line.models import EventModel
from my_diary.manager import MyDiaryManager
from reminder.manager import ReminderManager
from user.cache import AppCache
from user.manager import UserSettingManager
from user.models import CustomUserModel


class ApiAiData(object):
    def __init__(self, response: HTTPResponse):
        self._response = json.loads(response.read().decode('utf-8'))

    @property
    def action(self) -> str:
        return self._response['result']['action']

    @property
    def intent(self) -> str:
        return self._response['result']['metadata']['intentName']

    @property
    def response_text(self) -> str:
        return self._response['result']['fulfillment']['messages'][0]['speech']

    @property
    def parameters(self) -> Union[dict, str]:
        return self._response['result']['parameters']

    @property
    def is_action_incomplete(self) -> bool:
        return self._response['result']['actionIncomplete']

    @property
    def is_unknown_intent(self) -> bool:
        return self.intent == 'Debby.unknown'


class InputHandler(object):
    def __init__(self, line_id: str):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.text = ''
        self.image_id = ''
        self.api_ai = self.setup_api_ai()

        self.registered_actions = {
            "ask.food": self.handle_food_ask,
            "smalltalk": self.reply_api_ai_text_response,
            'record.bg': self.handle_bg_record,
            "record.food": self.handle_food_record,
        }
        self.ai_data = None  # type: ApiAiData
        self.chatbase_set = MessageSet(api_key=settings.CHATBASE_AGENT_KEY,
                                       platform='Line',
                                       version='1',
                                       user_id=line_id)

    @staticmethod
    def setup_api_ai():
        ai = apiai.ApiAI(settings.CLIENT_ACCESS_TOKEN)
        return ai

    @staticmethod
    def is_answer_in_consult_food(name):
        return SynonymModel.objects.search_by_synonym(name).count()

    def new_bot_reply(self, send_message: SendMessage):
        if isinstance(send_message, TextSendMessage):
            bot_reply = self.chatbase_set.new_message(message=send_message.text)  # type: base_message.Message
            bot_reply.set_as_type_agent()
            not_handled_situations = ['Debby 找不到', '您輸入的血糖範圍好像怪怪的', '我猜你不是要輸入血糖齁！', '我猜你不是要輸入血糖齁！']

            for s in not_handled_situations:
                if send_message.text.startswith(s):
                    user_message = self.chatbase_set.messages[0]   # type: base_message.Message
                    if user_message.type == MessageTypes.USER:
                        user_message.set_as_not_handled()

        elif isinstance(send_message, TemplateSendMessage):
            bot_reply = self.chatbase_set.new_message(
                message=send_message.as_json_string())  # type: base_message.Message
            bot_reply.set_as_type_agent()

        elif isinstance(send_message, list):
            for message in send_message:
                if isinstance(message, TextSendMessage):
                    bot_reply = self.chatbase_set.new_message(
                        message=message.text)  # type: base_message.Message
                    bot_reply.set_as_type_agent()
                if isinstance(message, TemplateSendMessage):
                    bot_reply = self.chatbase_set.new_message(
                        message=message.as_json_string())  # type: base_message.Message
                    bot_reply.set_as_type_agent()
        else:
            print(type(send_message))
            raise ValueError('not implement error')

    def find_best_answer_for_text(self) -> SendMessage:
        """
        Mainly response for replying.
        There will be four conditions:
        1. input text is founded in database (ex: chat conversation)
        2. input is digits, which is might be blood glucose value
        3. continuous conversation, the cache record which app is currently used.
        4. input that debby can not recognized.

        :return: SendMessage
        """
        app_cache = AppCache(self.line_id)
        special_case = ["血糖紀錄", "飲食紀錄", "食物熱量查詢", "藥物資訊查詢", "我的設定", "我的日記", "Go, Debby!"]

        if app_cache.is_app_running() and self.text not in special_case:
            print('Start from app_cache', app_cache.line_id, app_cache.app, app_cache.action)
            callback = Callback(line_id=self.line_id,
                                app=app_cache.app,
                                action=app_cache.action,
                                text=self.text)
            intent = app_cache.app + '-' + app_cache.action
            self.chatbase_set.new_message(intent=intent,
                                          message=self.text)  # type: base_message.Message
            send_message = CallbackHandler(callback).handle()
            return send_message

        if self.text not in special_case:
            request = self.api_ai.text_request()
            request.session_id = self.line_id
            request.query = self.text
            response = request.getresponse()
            self.ai_data = ApiAiData(response)

            user_msg = self.chatbase_set.new_message(intent=self.ai_data.intent,
                                                     message=self.text)  # type: base_message.Message
            if self.ai_data.is_unknown_intent:
                user_msg.set_as_not_handled()

            if self.ai_data.is_action_incomplete:
                send_message = self.reply_api_ai_text_response()
                return send_message

            action = self.ai_data.action

            registered_action = self.find_registered_actions(action)
            if action != "input.unknown":
                if registered_action:
                    send_message = registered_action()
                    return send_message

        events = EventModel.objects.filter(phrase=self.text)
        if not events:
            events = EventModel.objects.filter(phrase__iexact=self.text)

        # event founded in event model(app, action)
        if events:
            event = random.choice(events)
            print(event.callback, event.action)

            callback = Callback(line_id=self.line_id,
                                app=event.callback,
                                action=event.action,
                                text=self.text)
            intent = callback.app + '-' + callback.action
            self.chatbase_set.new_message(intent=intent,
                                          message=self.text)  # type: base_message.Message

            send_message = CallbackHandler(callback).handle()
            if send_message:
                return send_message
            else:
                return TextSendMessage(text='哀呀, Debby 犯傻了><')

        # user might input number directly.
        elif self.text.isdigit():
            print('user input digit', self.text)
            callback = BGRecordCallback(line_id=self.line_id,
                                        action=BGRecordAction.CREATE_FROM_VALUE,
                                        text=self.text)

            intent = callback.app + '-' + callback.action
            self.chatbase_set.new_message(intent=intent,
                                          message=self.text)  # type: base_message.Message

            send_message = CallbackHandler(callback).handle()
            return send_message

        elif self.is_answer_in_consult_food(self.text):
            callback = ConsultFoodCallback(line_id=self.line_id,
                                           action=ConsultFoodAction.READ,
                                           text=self.text)

            intent = callback.app + '-' + callback.action
            self.chatbase_set.new_message(intent=intent,
                                          message=self.text)  # type: base_message.Message

            send_message = CallbackHandler(callback).handle()
            return send_message

        # Debby can't understand what user saying.
        else:
            send_message = self.reply_api_ai_text_response()
            return send_message

    def handle_image(self, image_id):
        app_cache = AppCache(self.line_id)
        callback = None
        if app_cache.is_app_running():
            if app_cache.app == App.FOOD_RECORD:
                callback = FoodRecordCallback(self.line_id,
                                              action=FoodRecordAction.DIRECT_UPLOAD_IMAGE,
                                              image_id=image_id)
            elif app_cache.app == App.MY_DIARY:
                callback = MyDiaryCallback(self.line_id,
                                           action=MyDiaryAction.UPDATE_FOOD_PHOTO_CHECK,
                                           image_id=image_id)
        else:  # directly upload image
            callback = FoodRecordCallback(self.line_id,
                                          action=FoodRecordAction.DIRECT_UPLOAD_IMAGE,
                                          image_id=image_id)
        intent = callback.app + '-' + callback.action
        self.chatbase_set.new_message(intent=intent, message=self.text)
        return CallbackHandler(callback).handle()

    def handle_postback(self, data):
        data_dict = dict(parse_qsl(data))
        callback = Callback(**data_dict) if data_dict.get("line_id") else Callback(line_id=self.line_id, **data_dict)

        intent = callback.app + '-' + callback.action
        self.chatbase_set.new_message(intent=intent,
                                      message=self.text)  # type: base_message.Message

        send_message = CallbackHandler(callback).handle()
        self.new_bot_reply(send_message)
        self.chatbase_set.send()
        return send_message

    def find_registered_actions(self, action: str):
        first_split_action_name = action.split('.')[0]
        if action in self.registered_actions:
            return self.registered_actions[action]
        elif first_split_action_name in self.registered_actions:
            return self.registered_actions[first_split_action_name]
        else:
            return None

    def handle(self, message: Message):
        send_message = None
        if isinstance(message, TextMessage):
            self.text = message.text
            send_message = self.find_best_answer_for_text()
            self.new_bot_reply(send_message)

        elif isinstance(message, ImageMessage):
            send_message = self.handle_image(message.id)
            self.new_bot_reply(send_message)

        print(self.chatbase_set.send())
        return send_message

    def reply_api_ai_text_response(self):
        print('reply_api_ai_text_response')
        text = self.ai_data.response_text
        return TextSendMessage(text=text)

    """
    Handle api.ai actions
    """

    def handle_food_ask(self):
        print('handle_food_ask')
        food_name = self.ai_data.parameters['food_name'][0]
        callback_data = ConsultFoodCallback(self.line_id,
                                            action=ConsultFoodAction.READ,
                                            text=food_name)
        reply = CallbackHandler(callback_data).handle()
        return reply

    def handle_bg_record(self):
        print('handle_bg_record')
        number = self.ai_data.parameters["number"]
        bg_record_time = self.ai_data.parameters['bg-record-time']

        choice = None
        if bg_record_time == '餐前':
            choice = 'before'
        elif bg_record_time == '餐後':
            choice = 'after'

        glucose_val = utils.to_number(number)

        callback_data = BGRecordCallback(self.line_id,
                                         action=BGRecordAction.SET_TYPE,
                                         choice=choice,
                                         glucose_val=glucose_val)
        return CallbackHandler(callback_data).handle()

    def handle_food_record(self):
        print('handle_food_record')
        callback_data = FoodRecordCallback(self.line_id,
                                           action=FoodRecordAction.CREATE_FROM_MENU)
        return CallbackHandler(callback_data).handle()

    """
    Handle api.ai actions end
    """


class CallbackHandler(object):
    """
    Distribute the tasks (ex: the query result from EventModel) to corresponding App.manager
    """
    image_content = bytes()

    class App(object):
        def __init__(self, manager, callback):
            self.manager = manager
            self.callback = callback

    def __init__(self, callback: Callback):
        self.callback = callback
        self.registered_app = [
            self.App(BGRecordManager, BGRecordCallback),
            self.App(ChatManager, ChatCallback),
            self.App(ConsultFoodManager, ConsultFoodCallback),
            self.App(DrugAskManager, DrugAskCallback),
            self.App(FoodRecordManager, FoodRecordCallback),
            self.App(ReminderManager, ReminderCallback),
            self.App(UserSettingManager, UserSettingsCallback),
            self.App(MyDiaryManager, MyDiaryCallback),
            self.App(LineManager, LineCallback),
        ]

    def handle(self) -> Union[SendMessage, None]:
        """
        First convert the input Callback to proper type of Callback, then run the manager.
        """

        print("{}, {}\n".format(self.callback.app, self.callback.action))

        for app in self.registered_app:
            if self.callback == app.callback:
                callback = self.callback.convert_to(app.callback)
                manager = app.manager(callback)
                return manager.handle()
        else:
            print('not find corresponding app.')
            return None
