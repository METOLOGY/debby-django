import re
from collections import deque
from typing import List, Union

from django.core.cache import cache
from django.db.models import QuerySet
from linebot.models import SendMessage, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate, ImageSendMessage
from linebot.models import TextSendMessage

from consult_food.models import FoodModel, TaiwanSnackModel, ICookIngredientModel, ICookDishModel
from debby import utils
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
    def reply_food_nutrition(content_model):
        count_word = utils.get_count_word(content_model)
        return utils.reply_nutrition(count_word, content_model.nutrition)

    @staticmethod
    def reply_content(url: str, preview_url: str) -> List[Union[TextSendMessage, ImageSendMessage]]:
        text = TextSendMessage(text="每100克")
        host = cache.get("host_name")
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)
        calories = ImageSendMessage(original_content_url=photo,
                                    preview_image_url=preview_photo)

        return [text, calories]

    def read_from_menu(self, app_cache: AppCache) -> TextSendMessage:
        app_cache.set_next_action(self.callback.app, action=Action.READ)
        app_cache.commit()
        return TextSendMessage(text="好的😚！請告訴我食品的名稱:")

    def find_in_food_name_model(self, name: str):
        queries = FoodModel.objects.search_by_name(name)
        if not queries:
            queries = FoodModel.objects.search_by_synonyms(name)
        if len(queries) > 20:
            queries = queries[:20]
        if len(queries) > 1:
            reply = self.ask_which_one(queries)
        elif len(queries) == 1:
            food = queries[0]
            reply = self.reply_food_nutrition(food)
        else:
            reply = None
        return reply

    def ask_which_one(self, queries: QuerySet) -> List[TemplateSendMessage]:
        card_num_list = get_each_card_num(len(queries))
        reply = list()
        message = "請問您要查閱的是:"
        d = deque(queries)
        labels = []
        for card_num in card_num_list:
            actions = []
            for i in range(card_num):
                query = d.popleft()
                if isinstance(query, TaiwanSnackModel):
                    place = query.place.rstrip('小吃').rstrip('伴手禮')
                    label = "{}的{}".format(place, query.name)
                    if label in labels:
                        number_string_list = re.findall(r'\d+', label)
                        if not number_string_list:
                            label += " (2)"
                        else:
                            num = int(number_string_list[0])
                            label += " ({})".format(num)
                    else:
                        labels.append(label)
                    actions.append(
                        PostbackTemplateAction(
                            label=label,
                            data=ConsultFoodCallback(
                                line_id=self.callback.line_id,
                                action=Action.WAIT_SNACK_NAME_CHOICE,
                                food_id=query.id
                            ).url
                        )
                    )
                elif isinstance(query, FoodModel):
                    actions.append(
                        PostbackTemplateAction(
                            label=query.sample_name,
                            data=ConsultFoodCallback(
                                line_id=self.callback.line_id,
                                action=Action.WAIT_FOOD_NAME_CHOICE,
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

    def find_in_taiwan_snack(self, name: str):
        reply = None
        queries = TaiwanSnackModel.objects.search_by_name(name)
        if not queries:
            queries = TaiwanSnackModel.objects.search_by_synonyms(name)

        if not queries:
            reply = None
        else:
            if len(queries) == 1:
                snack = queries[0]
                reply = self.reply_food_nutrition(snack)
            elif len(queries) > 1:
                reply = self.ask_which_one(queries)

        return reply

    def find_in_i_cook_ingredient(self, name: str):
        reply = None

        results = ICookIngredientModel.objects.search_by_name(name)
        if not results:
            results = ICookIngredientModel.objects.search_by_synonyms(name)
        if results:
            ingredient = results[0]
            reply = self.reply_food_nutrition(ingredient)
        return reply

    def find_in_i_cook_dish(self, name: str):
        reply = None

        queries = ICookDishModel.objects.search_by_name(name)
        if not queries:
            queries = ICookDishModel.objects.search_by_synonyms(name)
        if queries:
            dish = queries[0]
            reply = self.reply_food_nutrition(dish)
        return reply

    def read(self, app_cache: AppCache):
        print(Action.READ)
        app_cache.delete()
        name = self.callback.text
        find_order = [
            self.find_in_taiwan_snack,
            self.find_in_i_cook_dish,
            self.find_in_food_name_model,
            self.find_in_i_cook_ingredient,
        ]
        reply = None
        for find_in in find_order:
            reply = find_in(name)
            if reply:
                break
        if not reply:
            reply = TextSendMessage(text="Debby 找不到您輸入的食物{}，試試其他的?".format(name))
        return reply

    def wait_food_name_choice(self, app_cache: AppCache):
        food = FoodModel.objects.get(pk=self.callback.food_id)
        return self.reply_food_nutrition(food)

    def wait_snack_food_name_choice(self, app_cache: AppCache):
        snack = TaiwanSnackModel.objects.get(pk=self.callback.food_id)
        return self.reply_food_nutrition(snack)

    def handle(self) -> SendMessage:
        app_cache = AppCache(self.callback.line_id)
        return self.registered_actions[self.callback.action](app_cache)
