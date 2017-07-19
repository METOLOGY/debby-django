from collections import deque
from itertools import chain
from typing import List

from django.db.models import QuerySet
from linebot.models import SendMessage, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate
from linebot.models import TextSendMessage

from consult_food.models import FoodNameModel, FoodModel, TaiwanSnackModel
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
            Action.WAIT_FOOD_NAME_CHOICE: self.wait_food_name_choice,
            Action.WAIT_SNACK_NAME_CHOICE: self.wait_snack_food_name_choice
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

    @staticmethod
    def reply_snack_content(snack: TaiwanSnackModel) -> TextSendMessage:
        text = "{}重{}g, 熱量為{}kcal, 蔬菜類{}份, 水果類{}份, 蛋豆魚肉類{}份, 全榖根莖類{}份, 低脂乳品類{}份, 油脂與堅果種子類{}份".format(
            snack.name,
            snack.nutrition.gram,
            snack.nutrition.calories,
            snack.nutrition.vegetable_amount,
            snack.nutrition.fruit_amount,
            snack.nutrition.protein_food_amount,
            snack.nutrition.grain_amount,
            snack.nutrition.diary_amount,
            snack.nutrition.oil_amount
        )
        return TextSendMessage(text=text)

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

    def find_in_food_name_model(self):
        food_names = FoodNameModel.objects.filter(
            known_as_name=self.callback.text).distinct("food__sample_name")
        distinct_food_names = []

        # if len(food_names) < 20:
        #     reverse_search_food_names = FoodNameModel.objects.extra(where=["%s LIKE CONCAT('%%',known_as_name,'%%')"],
        #                                                             params=[self.callback.text])
        #     reverse_search_food_names = reverse_search_food_names.distinct('food__sample_name')
        #     food_names = list(chain(food_names, reverse_search_food_names))
        #     distinct_food_names_id = []
        #     for ind, food_name in enumerate(food_names):
        #         if food_name.id not in distinct_food_names_id:
        #             distinct_food_names_id.append(food_name.id)
        #             distinct_food_names.append(food_name)
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
            reply = None
        return reply

    def ask_which_one(self, queries: QuerySet) -> List[TemplateSendMessage]:
        card_num_list = get_each_card_num(len(queries))
        reply = list()
        message = "請問您要查閱的是:"
        d = deque(queries)
        for card_num in card_num_list:
            actions = []
            for i in range(card_num):
                query = d.popleft()
                if isinstance(query, TaiwanSnackModel):
                    actions.append(
                        PostbackTemplateAction(
                            label=query.name,
                            data=ConsultFoodCallback(
                                line_id=self.callback.line_id,
                                action=Action.WAIT_SNACK_NAME_CHOICE,
                                food_id=query.id
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
        return reply

    def find_in_taiwan_snack(self):
        def only_one_result(_results):
            return len(_results) == 1

        def more_than_one_results(_results):
            return len(_results) > 1

        reply = None
        name = self.callback.text
        results = TaiwanSnackModel.objects.search_by_name(name)
        if results:
            snack = results[0]
            reply = self.reply_snack_content(snack)
        else:
            results = TaiwanSnackModel.objects.search_by_synonym(name)
            if more_than_one_results(results):
                reply = self.ask_which_one(results)
            elif only_one_result(results):
                snack = results[0]
                reply = self.reply_snack_content(snack)

        return reply

    def read(self, app_cache: AppCache):
        app_cache.delete()
        find_order = [
            self.find_in_taiwan_snack,
            self.find_in_food_name_model
        ]
        reply = None
        for find_in in find_order:
            reply = find_in()
            if reply:
                break
        if not reply:
            reply = TextSendMessage(text="Debby 找不到您輸入的食物喔，試試其他的?")
        return reply

    def wait_food_name_choice(self, app_cache: AppCache):
        food = FoodModel.objects.get(pk=self.callback.food_id)
        return self.reply_content(food)

    def wait_snack_food_name_choice(self, app_cache: AppCache):
        snack = TaiwanSnackModel.objects.get(pk=self.callback.food_id)
        return self.reply_snack_content(snack)

    def handle(self) -> SendMessage:
        app_cache = AppCache(self.callback.line_id)
        return self.registered_actions[self.callback.action](app_cache)
