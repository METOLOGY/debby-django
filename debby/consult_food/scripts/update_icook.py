from typing import List

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from consult_food.models import NutritionTuple, ICookDishModel
from consult_food.scripts.create_icook_model import read_dishes, Ingredient, Dish, get_nutrition_list_from_ingredients, \
    calculate_dish_nutrition


def update_i_cook_dish_model(dish: Dish, nutrition_list: List[NutritionTuple]) -> bool:
    status = False
    try:
        dish_model = ICookDishModel.objects.get(source_url=dish.source_url)
    except (ObjectDoesNotExist, MultipleObjectsReturned) as err:
        print(err)
        print(dish.name)
        return status

    nutrition = calculate_dish_nutrition(dish.name, nutrition_list)
    nutrition_model = dish_model.nutrition

    nutrition_model.fruit_amount = nutrition.fruit_amount
    nutrition_model.vegetable_amount = nutrition.vegetable_amount
    nutrition_model.grain_amount = nutrition.grain_amount
    nutrition_model.protein_food_amount = nutrition.protein_food_amount
    nutrition_model.diary_amount = nutrition.diary_amount
    nutrition_model.oil_amount = nutrition.oil_amount
    nutrition_model.gram = nutrition.gram
    nutrition_model.calories = nutrition.calories
    nutrition_model.protein = nutrition.protein
    nutrition_model.fat = nutrition.fat
    nutrition_model.carbohydrates = nutrition.carbohydrates
    nutrition_model.save()

    if nutrition_model.is_six_group_image_created():
        nutrition_model.delete_six_group_image()
    nutrition_model.make_and_save_calories_image()
    nutrition_model.save()

    status = True

    return status


def run():
    """
    目的有:
    讀取新的數據, 在db中找到他, 更新db中的數據, 更新db中的圖片
    """
    raw_dishes = read_dishes()

    for raw_dish in raw_dishes:
        ingredients = [Ingredient(**i) for i in raw_dish['ingredients']]
        dish = Dish(**raw_dishes)
        dish = dish._replace(ingredients=ingredients)

        print('Dish: %s' % dish.name)

        nutrition_list = get_nutrition_list_from_ingredients(dish.ingredients)
        if not nutrition_list:
            continue

        status = update_i_cook_dish_model(dish, nutrition_list)
