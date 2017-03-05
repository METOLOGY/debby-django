from linebot.models import SendMessage

from bg_record.manager import BGRecordManager


class InputHandler(object):
    bg_manager = BGRecordManager('', '')

    def __init__(self, input_text: str):
        self.input_text = input_text

    def is_input_a_bg_value(self):
        return self.input_text.isdigit()

    def find_best_answer(self):
        if self.is_input_a_bg_value():
            return self.bg_manager.reply_record_success()
        else:
            return self.bg_manager.reply_does_user_want_to_record()

    def dispatch(self):
        answer = self.find_best_answer()
