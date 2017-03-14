from urllib.parse import parse_qsl

from django.core.cache import cache
from hamcrest import *
from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

from bg_record.manager import BGRecordManager
from food_record.manager import FoodRecordManager
from line.callback import FoodRecordCallback, Callback, BGRecordCallback
from line.models import EventModel
from user.models import CustomUserModel


class InputHandler(object):
    def __init__(self, line_id: str, message: Message):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.message = message
        self.text = ''

    def is_input_a_bg_value(self):
        return self.text.isdigit()

    def find_best_answer_for_text(self) -> SendMessage:
        user_cache = cache.get(self.line_id)
        event = EventModel.objects.get_or_none(phrase=self.text)

        callback_url = Callback(line_id=self.line_id).url
        bg_manager = BGRecordManager(callback_url)

        if self.is_input_a_bg_value():
            bg_manager.record_bg_record(self.current_user, int(self.text))
            return bg_manager.reply_record_success()
        elif event:
            callback_url = Callback(line_id=self.line_id,
                                    app=event.callback,
                                    action=event.action).url
            return CallbackHandler(callback_url).handle()
        elif user_cache and 'food_record_pk' in user_cache.keys():
            callback_url = FoodRecordCallback(self.line_id,
                                              action='UPDATE',
                                              choice='true',
                                              text=self.text).url
            return CallbackHandler(callback_url).handle()
        else:
            return bg_manager.reply_does_user_want_to_record()

    def handle(self):
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()


class CallbackHandler(object):
    image_content = bytes()

    def __init__(self, callback_url: str):
        self.callback = Callback.decode(callback_url)

    def is_callback_from_food_record(self):
        return self.callback == FoodRecordCallback and self.callback.action == 'CREATE'

    def setup_for_record_food_image(self, image_content: bytes):
        self.image_content = image_content

    def handle(self) -> SendMessage:
        if self.callback == BGRecordCallback:
            callback = self.callback.transfer_to(BGRecordCallback)
            bg_manager = BGRecordManager(callback)
            return bg_manager.handle()
        elif self.callback == FoodRecordCallback:
            callback = self.callback.transfer_to(FoodRecordCallback)
            fr_manager = FoodRecordManager(callback, self.image_content)
            return fr_manager.handle()
