from urllib.parse import parse_qsl

from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage

from bg_record.manager import BGRecordManager
from food_record.manager import FoodRecordManager
from user.models import CustomUserModel


class InputHandler(object):
    bg_manager = BGRecordManager()
    food_manager = FoodRecordManager

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
        return self.food_manager.reply_if_user_want_to_record()

    def handle(self):
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()
        elif isinstance(self.message, ImageMessage):
            return self.trigger_manager_to_reply()



class CallbackHandler(object):
    bg_manager = BGRecordManager()
    food_manager = FoodRecordManager('', '')

    def __init__(self, input_data):
        data = dict(parse_qsl(input_data))
        self.data = data
        self.callback = data['callback']
        self.action = data['action']

    def handle(self) -> SendMessage:
        if self.callback == 'BGRecord':
            if self.action == 'record_bg':
                return self.bg_manager.reply_to_user_choice(self.data)
        elif self.callback == 'FoodRecord':
            if self.action == 'record':
                return self.food_manager.reply_if_user_want_to_record()
