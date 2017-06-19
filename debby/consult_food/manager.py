import math
from collections import deque

from linebot.models import SendMessage, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate
from linebot.models import TextSendMessage

from consult_food.models import ConsultFoodModel, FoodNameModel, FoodModel
from debby.utils import get_each_card_num
from line.callback import ConsultFoodCallback
from line.constant import ConsultFoodAction as Action
from user.cache import AppCache


class ConsultFoodManager(object):
    def __init__(self, callback: ConsultFoodCallback):
        self.callback = callback
        self.registered_actions = {
            Action.READ_FROM_MENU: self.read_from_menu,
            Action.READ: self.read,
            Action.WAIT_FOOD_NAME_CHOICE: self.wait_food_name_choice
        }

    @staticmethod
    def reply_content(food: FoodModel) -> TextSendMessage:
        return TextSendMessage(
            text="每100克{}含有\n熱量{}大卡\n含可代謝醣類{}克\n蛋白質{}克\n脂質{}克".format(
                food.sample_name,
                food.modified_calorie,
                food.metabolic_carbohydrates,
                food.crude_protein,
                food.crude_fat
            )
        )

    def read_from_menu(self, app_cache: AppCache) -> TextSendMessage:
        app_cache.set_next_action(self.callback.app, action=Action.READ)
        app_cache.commit()
        return TextSendMessage(text="請輸入食品名稱:")

    def read(self, app_cache: AppCache):
        app_cache.delete()
        food_names = FoodNameModel.objects.filter(known_as_name=self.callback.text)
        if len(food_names) > 1:

            card_num_list = get_each_card_num(len(food_names))
            reply = list()
            message = "請問您要查閱的是："
            d = deque(food_names)
            for card_num in card_num_list:
                actions = []
                for i in range(card_num):
                    food_name = d.popleft()  # type: FoodNameModel

                    actions.append(
                        PostbackTemplateAction(
                            label=food_name.food.sample_name,
                            data=ConsultFoodCallback(
                                line_id=self.callback.line_id,
                                action=Action.WAIT_FOOD_NAME_CHOICE,
                                food_id=food_name.food.id
                            ).url
                        )
                    )
                template_send_message = TemplateSendMessage(
                    alt_text=message,
                    template=ButtonsTemplate(
                        text=message,
                        actions=actions
                    )
                )
                reply.append(template_send_message)
        elif len(food_names) == 1:
            food = food_names[0].food
            reply = self.reply_content(food)
        else:
            reply = TextSendMessage(text="Debby 找不到您輸入的食物喔，試試其他的?")
        return reply

    def wait_food_name_choice(self, app_cache: AppCache):
        food = FoodModel.objects.get(pk=self.callback.food_id)
        return self.reply_content(food)

    def handle(self) -> SendMessage:
        app_cache = AppCache(self.callback.line_id)
        return self.registered_actions[self.callback.action](app_cache)
