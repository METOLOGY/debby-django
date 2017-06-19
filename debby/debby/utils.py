import math


# find how many template needed
def get_each_card_num(choice_num: int) -> list:
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
