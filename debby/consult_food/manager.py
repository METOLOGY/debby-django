from linebot.models import TextSendMessage

from consult_food.models import ConsultFoodModel
from line.callback import ConsultFoodCallback


class ConsultFoodManager(object):
    def __init__(self, callback: ConsultFoodCallback, input_text: str):
        self.callback = callback
        self.text = input_text

    def reply_answer(self):
        food = ConsultFoodModel.objects.get(sample_name=self.text)
        sample_name = food.sample_name
        modified_calorie = food.modified_calorie
        metabolic_carbohydrates = food.metabolic_carbohydrates
        carbohydrates_equivalent = food.carbohydrates_equivalent
        white_rice_equivalent = food.white_rice_equivalent
        message = "每100克{}含有: 熱量{}大卡，含可代謝醣類{}克，等於{}份醣類，也代表吃了{}碗白飯".format(sample_name,
                                                                          modified_calorie,
                                                                          metabolic_carbohydrates,
                                                                          carbohydrates_equivalent,
                                                                          white_rice_equivalent)
        return TextSendMessage(text=message)

    def handle(self):
        self.reply_answer()
