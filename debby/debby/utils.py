import json
import math
# find how many template needed
from typing import List, Union

from django.core.cache import cache
from linebot.models import ImageSendMessage, TextSendMessage

from consult_food.models import NutritionModel, SynonymModel, FoodModel, TaiwanSnackModel, ICookIngredientModel, \
    ICookDishModel


def get_each_card_num(choice_num: int) -> List[int]:
    def find_card_len(num):
        return math.ceil(num / 4)

    def find_button_num(num, _card_len):
        return math.ceil(num / _card_len)

    result = []
    while choice_num > 0:
        card_len = find_card_len(choice_num)
        button_num = find_button_num(choice_num, card_len)
        result.append(button_num)
        choice_num -= button_num
    return result


def load_from_json_file(file_path: str) -> Union[list, dict]:
    with open(file_path, encoding='utf-8') as file:
        j = json.load(file)
    return j


def save_to_json_file(file_path: str, data):
    with open(file_path, 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=4)


def is_future_mode_on(line_id: str):
    return cache.get(line_id + '_future')


def is_demo_mode_on(line_id: str):
    return cache.get(line_id + '_demo')


def reply_nutrition(count_word: str, nutrition: NutritionModel) -> List[Union[TextSendMessage, ImageSendMessage]]:
    reply = list()

    text_message = TextSendMessage(text=count_word)
    reply.append(text_message)

    url = nutrition.nutrition_amount_image.url
    preview_url = nutrition.nutrition_amount_image_preview.url

    host = cache.get("host_name")
    photo = "https://{}{}".format(host, url)
    preview_photo = "https://{}{}".format(host, preview_url)
    calories = ImageSendMessage(original_content_url=photo,
                                preview_image_url=preview_photo)
    reply.append(calories)

    if nutrition.is_six_group_valid():
        url = nutrition.six_group_portion_image.url
        preview_url = nutrition.six_group_portion_image_preview.url

        host = cache.get("host_name")
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)
        six_group = ImageSendMessage(original_content_url=photo,
                                     preview_image_url=preview_photo)
        reply.append(six_group)

    return reply


def get_count_word(content_model: object):
    if isinstance(content_model, FoodModel):
        return "每{}克".format(int(content_model.nutrition.gram))
    elif isinstance(content_model, TaiwanSnackModel):
        return "每{}".format(content_model.count_word)
    elif isinstance(content_model, ICookIngredientModel):
        return "每{}克".format(int(content_model.nutrition.gram))
    elif isinstance(content_model, ICookDishModel):
        return "每{}".format(content_model.count_word)
