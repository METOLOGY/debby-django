import random

from linebot.models import SendMessage
from linebot.models import TextSendMessage

from chat.models import ChatModel
from line.callback import ChatCallback


class ChatManager(object):
    chats = []

    def __init__(self, callback: ChatCallback):
        self.callback = callback

    def is_input_a_chat(self, text: str):
        chats = ChatModel.objects.filter(phrase=text)
        self.chats = chats
        if chats:
            return True
        else:
            return False

    def reply_answer(self) -> TextSendMessage:
        chat = random.choice(self.chats)  # type: ChatModel
        message = chat.answer
        return TextSendMessage(text=message)

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')

        print('chat: ', self.callback.text)
        #TODO: 會有action不是read的情況出現嗎？
        # if self.callback.action == 'READ':
        if self.is_input_a_chat(self.callback.text):
            reply = self.reply_answer()
        else:
            reply = TextSendMessage(text='我猜你不是要輸入血糖齁！原本想講個笑話給您聽的，但我不太清楚你說了什麼~')

        return reply
