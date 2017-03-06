from urllib.parse import parse_qsl

from linebot.models import SendMessage

from bg_record.manager import BGRecordManager
from user.models import CustomUserModel


class InputHandler(object):
    bg_manager = BGRecordManager()

    def __init__(self, current_user: CustomUserModel, input_text: str):
        self.current_user = current_user
        self.input_text = input_text

    def is_input_a_bg_value(self):
        return self.input_text.isdigit()

    def find_best_answer_for_text(self) -> SendMessage:
        if self.is_input_a_bg_value():
            self.bg_manager.record_bg_record(self.current_user, int(self.input_text))
            return self.bg_manager.reply_record_success()
        else:
            return self.bg_manager.reply_does_user_want_to_record()

    def handle(self):
        return self.find_best_answer_for_text()


class CallbackHandler(object):
    bg_manager = BGRecordManager()

    def __init__(self, input_data):
        data = dict(parse_qsl(input_data))
        self.data = data
        self.callback = data['callback']
        self.action = data['action']

    def handle(self) -> SendMessage:
        if self.callback == 'BGRecord':
            if self.action == 'record_bg':
                return self.bg_manager.reply_to_user_choice(self.data)
