from collections import deque
from typing import List, Union

from django.core.cache import cache
from django.db.models import QuerySet
from linebot.models import SendMessage, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate, ImageSendMessage
from linebot.models import TextSendMessage

from consult_food.models import FoodNameModel, FoodModel, TaiwanSnackModel, ICookIngredientModel
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
    def reply_content(url: str, preview_url: str) -> List[Union[TextSendMessage, ImageSendMessage]]:
        text = TextSendMessage(text="每100克")
        host = cache.get("host_name")
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)
        calories = ImageSendMessage(original_content_url=photo,
                                    preview_image_url=preview_photo)

        return [text, calories]

    def reply_food_content(self, food: FoodModel) -> List[Union[TextSendMessage, ImageSendMessage]]:
        url = food.nutrition.nutrition_amount_image.url
        preview_url = food.nutrition.nutrition_amount_image_preview.url

        return self.reply_content(url, preview_url)

    def reply_i_cook_ingredient_content(self, ingredient: ICookIngredientModel) -> \
            List[Union[TextSendMessage, ImageSendMessage]]:

        url = ingredient.nutrition.nutrition_amount_image.url
        preview_url = ingredient.nutrition.nutrition_amount_image_preview.url

        return self.reply_content(url, preview_url)

    @staticmethod
    def reply_snack_content(snack: TaiwanSnackModel) -> List[Union[TextSendMessage, ImageSendMessage]]:
        text = TextSendMessage(text="每一份")

        url = snack.nutrition.six_group_portion_image.url
        preview_url = snack.nutrition.six_group_portion_image_preview.url

        host = cache.get("host_name")
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)
        six_group = ImageSendMessage(original_content_url=photo,
                                     preview_image_url=preview_photo)

        url = snack.nutrition.nutrition_amount_image.url
        preview_url = snack.nutrition.nutrition_amount_image_preview.url

        host = cache.get("host_name")
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)
        calories = ImageSendMessage(original_content_url=photo,
                                    preview_image_url=preview_photo)

        return [text, calories, six_group]

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
        # distinct_food_names = []

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
        if len(food_names) > 1:

            card_num_list = get_each_card_num(len(food_names[:20]))
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
            reply = self.reply_food_content(food)
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

    def find_in_i_cook_ingredient(self):
        reply = None
        name = self.callback.text
        results = ICookIngredientModel.objects.search_by_name(name)
        if results:
            ingredient = results[0]
            reply = self.reply_i_cook_ingredient_content(ingredient)
        return reply

    def read(self, app_cache: AppCache):
        app_cache.delete()
        find_order = [
            self.find_in_taiwan_snack,
            self.find_in_food_name_model,
            self.find_in_i_cook_ingredient,
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
        return self.reply_food_content(food)

    def wait_snack_food_name_choice(self, app_cache: AppCache):
        snack = TaiwanSnackModel.objects.get(pk=self.callback.food_id)
        return self.reply_snack_content(snack)

    def handle(self) -> SendMessage:
        app_cache = AppCache(self.callback.line_id)
        return self.registered_actions[self.callback.action](app_cache)
