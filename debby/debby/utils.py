import json
import math

# find how many template needed
from typing import List, Union


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
