import math
from collections import deque
from itertools import chain

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

    def like_query(self):
        return FoodNameModel.objects.filter(
            known_as_name__contains=self.callback.text).distinct("food__sample_name")

    def reverse_like_query(self):
        return FoodNameModel.objects.extra(where=["%s LIKE CONCAT('%%',known_as_name,'%%')"],
                                           params=[self.callback.text])

    def read(self, app_cache: AppCache):
        app_cache.delete()
        food_names = FoodNameModel.objects.filter(
            known_as_name__contains=self.callback.text).distinct("food__sample_name")
        distinct_food_names = []

        if len(food_names) < 20:
            reverse_search_food_names = FoodNameModel.objects.extra(where=["%s LIKE CONCAT('%%',known_as_name,'%%')"],
                                                                    params=[self.callback.text])
            reverse_search_food_names = reverse_search_food_names.distinct('food__sample_name')
            food_names = list(chain(food_names, reverse_search_food_names))
            distinct_food_names_id = []
            for ind, food_name in enumerate(food_names):
                if food_name.id not in distinct_food_names_id:
                    distinct_food_names_id.append(food_name.id)
                    distinct_food_names.append(food_name)
        if len(distinct_food_names) > 1:

            card_num_list = get_each_card_num(len(distinct_food_names[:20]))
            reply = list()
            message = "請問您要查閱的是："
            d = deque(distinct_food_names)
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
