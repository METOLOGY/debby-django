from linebot.models import SendMessage
from linebot.models import TextSendMessage

from line.callback import DrugAskCallback


class DrugAskManager(object):
    def __init__(self, callback: DrugAskCallback):
        self.callback = callback

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        if self.callback.action == 'READ_FROM_MENU':
            reply = TextSendMessage(text="請輸入藥品名稱(中英文皆可):")
        return reply
