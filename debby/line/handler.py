from bg_record.manager import BGRecordManager


class InputHandler(object):
    bg_manager = BGRecordManager()

    def __init__(self, input_text: str):
        self.input_text = input_text

    def find_best_answer(self):
        return self.bg_manager.reply_does_user_want_to_record()

    def dispatch(self):
        pass
