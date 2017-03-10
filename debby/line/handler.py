from urllib.parse import parse_qsl

from django.core.cache import cache
from hamcrest import *
from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

import debby
from bg_record.manager import BGRecordManager
from debby.settings import line_bot_api
from food_record.manager import FoodRecordManager
from user.models import CustomUserModel


class InputHandler(object):
    bg_manager = BGRecordManager()
    fr_manager = FoodRecordManager

    def __init__(self, current_user: CustomUserModel, message: Message):
        self.current_user = current_user
        self.message = message
        self.text = ''

    def is_input_a_bg_value(self):
        return self.text.isdigit()

    def find_best_answer_for_text(self) -> SendMessage:
        if self.is_input_a_bg_value():
            self.bg_manager.record_bg_record(self.current_user, int(self.text))
            return self.bg_manager.reply_record_success()
        else:
            return self.bg_manager.reply_does_user_want_to_record()

    def trigger_manager_to_reply(self):
        return self.fr_manager.reply_if_user_want_to_record()

    def handle(self):
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()
        elif isinstance(self.message, ImageMessage):
            return self.trigger_manager_to_reply()


class CallbackHandler(object):
    bg_manager = BGRecordManager()
    fr_manager = FoodRecordManager('', '')
    data = None
    callback = None
    action = None

    line_id = ''
    current_user = None
    image_content = bytes()

    def set_postback_data(self, input_data):
        data = dict(parse_qsl(input_data))
        self.data = data
        self.callback = data['callback']
        self.action = data['action']

    def set_user_line_id(self, line_id):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)

    def set_image_content(self, image_content: bytes):
        self.image_content = image_content

    def is_callback_from_food_record(self):
        return self.callback == 'FoodRecord'

    def setup_for_record_food_image(self, current_user: CustomUserModel, image_content: bytes):
        self.current_user = current_user
        self.image_content = image_content

    def store_to_user_cache(self, food_record_pk):
        assert_that(self.line_id, not_none)
        user_cache = cache.get(self.line_id)
        if user_cache:
            user_cache['food_record_pk'] = food_record_pk
            cache.set(self.line_id, user_cache)

    def handle(self) -> SendMessage:
        if self.callback == 'BGRecord':
            if self.action == 'record_bg':
                return self.bg_manager.reply_to_user_choice(self.data)
        elif self.callback == 'FoodRecord':
            if self.action == 'record':
                if self.data['choice'] == 'true':
                    food_record_pk = self.fr_manager.record_image(self.current_user, self.image_content)
                    self.store_to_user_cache(food_record_pk)
                    return self.fr_manager.reply_record_success_and_if_want_more_detail()
                elif self.data['choice'] == 'false':
                    return TextSendMessage(text='什麼啊原來只是讓我看看啊')
            elif self.action == 'write_other_notes':

                return self.fr_manager.reply_to_record_detail_template(self.data)
