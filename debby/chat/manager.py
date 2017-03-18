import random

from linebot.models import TextSendMessage

from chat.models import ChatModel
from line.callback import ChatCallback


class ChatManager(object):
    chats = []

    def __init__(self, callback: ChatCallback, input_text: str):
        self.callback = callback
        self.input_text = input_text

    def is_input_a_chat(self, text: str):
        chats = ChatModel.objects.filter(phrase=text)
        self.chats = chats
        if chats:
            return True
        else:
            return False

    def reply_answer(self):
        chat = random.choice(self.chats)  # type: ChatModel
        message = chat.answer
        return TextSendMessage(text=message)

    def handle(self):
        if self.callback.action == 'READ':
            if self.is_input_a_chat(self.input_text):
                return self.reply_answer()