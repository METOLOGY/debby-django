import random
from typing import Union
from urllib.parse import parse_qsl

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
    DrugAskCallback, ReminderCallback, MyDiaryCallback

from line.models import EventModel
from my_diary.manager import MyDiaryManager
from user.cache import AppCache
from user.models import CustomUserModel


class InputHandler(object):
    def __init__(self, line_id: str, message: Message = None):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.message = message
        self.text = ''
        self.image_id = ''


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
            print('Start from app_cache', app_cache.line_id, app_cache.app, app_cache.action)
            callback = None
            if app_cache.app == "FoodRecord":
                callback = FoodRecordCallback(self.line_id,
                                              action=app_cache.action,
                                              text=self.text
                                              )
            elif app_cache.app == "DrugAsk":
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
            print(event.callback, event.action)

            callback = Callback(line_id=self.line_id,
                                app=event.callback,
                                action=event.action,
                                text=self.text)
            send_message = CallbackHandler(callback).handle()
            if send_message:
                return send_message
            else:
                return TextSendMessage(text='哀呀, Debby ><')

        # Debby can't understand what user saying.
        else:
            return TextSendMessage(text='抱歉！能請您在描述的精確一點嗎？盡量以單詞為主喔~')

    def handle_image(self, image_id):
        callback = FoodRecordCallback(self.line_id,
                                      action="DIRECT_UPLOAD_IMAGE",
                                      image_id=image_id)
        return CallbackHandler(callback).handle()

    def handle_postback(self, data):
        app_cache = AppCache(self.line_id)
        data_dict = dict(parse_qsl(data))
        c = Callback(line_id=self.line_id, **data_dict)
        if c.app == "FoodRecord" and not app_cache.is_app_running():  # not sure if this is a common rule for all apps
            return None
        return CallbackHandler(c).handle()

    def handle(self):
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()

        elif isinstance(self.message, ImageMessage):
            return self.handle_image(self.message.id)


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
            self.App(MyDiaryManager, MyDiaryCallback),
        ]

    def is_callback_from_food_record(self):
        return self.callback == FoodRecordCallback and self.callback.action == 'CREATE'

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

