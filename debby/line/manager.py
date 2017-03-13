from .models import QAModel
import random
from linebot.models import TextSendMessage


class ChatManger:

    @staticmethod
    def get_response_text(phrase) -> str:
        answers = QAModel.objects.filter(phrase)

        # randomly select a answer
        answer = answers[random(0, len(answers))].answer
        return TextSendMessage(text=answer)

