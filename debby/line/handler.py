import json
import random
from typing import Union
from urllib.parse import parse_qsl

import apiai
from django.core.cache import cache
from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

from bg_record.manager import BGRecordManager
from chat.manager import ChatManager
from consult_food.manager import ConsultFoodManager
from consult_food.models import TaiwanSnackModel, ICookIngredientModel, FoodModel
from debby import settings
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


class InputHandler(object):
    def __init__(self, line_id: str):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.text = ''
        self.image_id = ''
        self.api_ai = self.setup_api_ai()

        self.registered_actions = {
            "food.ask": self.reply_food_ask,
            "smalltalk": self.reply_text_response
        }

    @staticmethod
    def setup_api_ai():
        ai = apiai.ApiAI(settings.CLIENT_ACCESS_TOKEN)
        return ai

    @staticmethod
    def is_answer_in_consult_food(name):
        orders = [
            TaiwanSnackModel.objects.search_by_name,
            TaiwanSnackModel.objects.search_by_synonym,
            FoodModel.objects.search_by_name,
            FoodModel.objects.search_by_synonyms,
            ICookIngredientModel.objects.search_by_name,
            ICookIngredientModel.objects.search_by_synonym
        ]
        for order in orders:
            queries = order(name)
            if len(queries) >= 1:
                return True
        return False

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
            return CallbackHandler(callback).handle()

        future_mode = cache.get(self.line_id + '_future')
        if self.text not in special_case and future_mode:
            request = self.api_ai.text_request()
            request.session_id = self.line_id
            request.query = self.text
            response = request.getresponse()
            js = json.loads(response.read().decode('utf-8'))
            action = js['result']['action']
            registered_action = self.find_registered_actions(action)
            if action != "input.unknown":
                if registered_action:
                    send_message = registered_action(js)
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
            send_message = CallbackHandler(callback).handle()
            if send_message:
                return send_message
            else:
                return TextSendMessage(text='哀呀, Debby 犯傻了><')

        # user might input number directly.
        elif self.text.isdigit():
            print('user input digit', self.text)
            bg_callback = BGRecordCallback(line_id=self.line_id,
                                           action=BGRecordAction.CREATE_FROM_VALUE,
                                           text=self.text)

            return CallbackHandler(bg_callback).handle()

        elif self.is_answer_in_consult_food(self.text):
            callback = ConsultFoodCallback(line_id=self.line_id,
                                           action=ConsultFoodAction.READ,
                                           text=self.text)
            return CallbackHandler(callback).handle()

        # Debby can't understand what user saying.
        else:
            if future_mode:
                send_message = self.reply_text_response(js)
                return send_message
            else:
                return TextSendMessage(text='抱歉！能請您在描述的精確一點嗎？盡量以單詞為主喔~')

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
        return CallbackHandler(callback).handle()

    def handle_postback(self, data):
        data_dict = dict(parse_qsl(data))
        callback = Callback(**data_dict) if data_dict.get("line_id") else Callback(line_id=self.line_id, **data_dict)
        return CallbackHandler(callback).handle()

    def handle(self, message: Message):
        if isinstance(message, TextMessage):
            self.text = message.text
            return self.find_best_answer_for_text()

        elif isinstance(message, ImageMessage):
            return self.handle_image(message.id)

    @staticmethod
    def reply_text_response(js: dict):
        print('reply_text_response')
        text = js['result']['fulfillment']['messages'][0]['speech']
        return TextSendMessage(text=text)

    def reply_food_ask(self, js: dict):
        print('reply_food_ask')
        food_name = js['result']['parameters']['food_name'][0]
        callback_data = ConsultFoodCallback(self.line_id,
                                            action=ConsultFoodAction.READ,
                                            text=food_name)
        return CallbackHandler(callback_data).handle()

    def find_registered_actions(self, action: str):
        first_split_action_name = action.split('.')[0]
        if action in self.registered_actions:
            return self.registered_actions[action]
        elif first_split_action_name in self.registered_actions:
            return self.registered_actions[first_split_action_name]
        else:
            return None



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
