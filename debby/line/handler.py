import random
from urllib.parse import parse_qsl

from django.core.cache import cache
from hamcrest import *
from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

from bg_record.manager import BGRecordManager
from chat.manager import ChatManager
from consult_food.manager import ConsultFoodManager
from drug_ask.manager import DrugAskManager
from food_record.manager import FoodRecordManager
from reminder.manager import ReminderManager
from line.callback import FoodRecordCallback, Callback, BGRecordCallback, ChatCallback, ConsultFoodCallback, \
    DrugAskCallback, ReminderCallback
from line.models import EventModel
from user.cache import AppCache, FoodData
from user.models import CustomUserModel


class InputHandler(object):
    def __init__(self, line_id: str, message: Message):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.message = message
        self.text = ''


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
        events = EventModel.objects.filter(phrase=self.text)

        if app_cache.is_app_running():
            callback = None
            print('Start from app_cache', app_cache.line_id, app_cache.app, app_cache.action)

            #TODO: unify the judgement
            if type(app_cache.data) is FoodData:
                callback = FoodRecordCallback(self.line_id,
                                              action='UPDATE',
                                              choice='true',
                                              text=self.text)
            elif app_cache.app is 'DrugAsk':
                callback = DrugAskCallback(self.line_id,
                                           action=app_cache.action,
                                           text=self.text)
            elif app_cache.app == 'BGRecord':
                callback = BGRecordCallback(self.line_id,
                                            action=app_cache.action,
                                            text=self.text)

            return CallbackHandler(callback).handle()

        # user might input number directly.
        elif self.text.isdigit():
            print('user input digit', self.text)
            bg_callback = BGRecordCallback(line_id=self.line_id, action='CREATE_FROM_VALUE', text=self.text)

            return CallbackHandler(bg_callback).handle()

        # event founded in event model(app, action)
        elif events:
            event = random.choice(events)
            print('Start from event', event.callback, event.action)

            callback = Callback(line_id=self.line_id,
                                app=event.callback,
                                action=event.action,
                                text=self.text)
            return CallbackHandler(callback).handle()

        # Debby can't understand what user saying.
        else:
            return TextSendMessage(text='哎呀，我不太清楚你說了什麼，你可以換句話說嗎 ~ ')

    def handle(self):
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()


class CallbackHandler(object):
    """
    Distribute the tasks (ex: the query result from EventModel) to corresponding App.manager
    """
    image_content = bytes()

    def __init__(self, callback: Callback):
        self.callback = callback

    def is_callback_from_food_record(self):
        return self.callback == FoodRecordCallback and self.callback.action == 'CREATE'

    def setup_for_record_food_image(self, image_content: bytes):
        self.image_content = image_content

    def handle(self) -> SendMessage:
        """
        First convert the input Callback to proper type of Callback, then run the manager.
        """

        if self.callback == BGRecordCallback:
            callback = self.callback.convert_to(BGRecordCallback)
            bg_manager = BGRecordManager(callback)
            return bg_manager.handle()

        elif self.callback == FoodRecordCallback:
            callback = self.callback.convert_to(FoodRecordCallback)
            fr_manager = FoodRecordManager(callback, self.image_content)
            return fr_manager.handle()

        elif self.callback == ChatCallback:
            callback = self.callback.convert_to(ChatCallback)
            chat_manager = ChatManager(callback)
            return chat_manager.handle()

        elif self.callback == ConsultFoodCallback:
            callback = self.callback.convert_to(ConsultFoodCallback)
            cf_manager = ConsultFoodManager(callback)
            return cf_manager.handle()

        elif self.callback == DrugAskCallback:
            callback = self.callback.convert_to(DrugAskCallback)
            da_manager = DrugAskManager(callback)
            return da_manager.handle()

        elif self.callback == ReminderCallback:
            callback = self.callback.convert_to(ReminderCallback)
            da_manager = ReminderManager(callback)
            return da_manager.handle()

        else:
            print('not find corresponding apps or callbacks.')
