from linebot.models import SendMessage
from linebot.models import TextSendMessage

from consult_food.models import ConsultFoodModel
from line.callback import ConsultFoodCallback


class ConsultFoodManager(object):
    def __init__(self, callback: ConsultFoodCallback):
        self.callback = callback

    def reply_answer(self) -> TextSendMessage:
        food = ConsultFoodModel.objects.get(sample_name=self.callback.text)
        sample_name = food.sample_name
        modified_calorie = food.modified_calorie
        metabolic_carbohydrates = food.metabolic_carbohydrates
        carbohydrates_equivalent = food.carbohydrates_equivalent
        white_rice_equivalent = food.white_rice_equivalent
        message = "每100克{}含有: 熱量{}大卡，含可代謝醣類{:.2f}克，等於{:.2f}份醣類，也代表吃了{:.2f}碗白飯".format(
            sample_name,
            modified_calorie,
            metabolic_carbohydrates,
            carbohydrates_equivalent,
            white_rice_equivalent
        )
        return TextSendMessage(text=message)

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='你說的是什麼食物呀，雖然我沒聽過，但感覺好像很好吃!')
        if self.callback.action == 'READ_FROM_MENU':
            reply = TextSendMessage(text="請輸入食品名稱:")
        else:
            reply = self.reply_answer()

        return reply
