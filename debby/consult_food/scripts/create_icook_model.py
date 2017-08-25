from typing import NamedTuple, Optional, List

from django.contrib.contenttypes.models import ContentType

from consult_food.models import SynonymModel, NutritionModel, ICookIngredientModel, ICookDishModel, NutritionTuple
from debby.utils import load_from_json_file


class Ingredient(NamedTuple):
    name: str
    gram: float


class Dish(NamedTuple):
    name: str
    source_url: str
    ingredients: List[Ingredient]


def read_dishes():
    return load_from_json_file('../chat_table/dishes.json')


def find_in_i_cook_ingredient_model(name: str) -> Optional[NutritionModel]:
    models = ICookIngredientModel.objects.filter(name=name)
    if models.count() == 0:
        return None
    elif models.count() >= 1:
        model = models[0]
        return model.nutrition


def find_in_synonym_model(name: str) -> Optional[NutritionModel]:
    models = SynonymModel.objects.search_by_synonyms(name)
    content_type = ContentType.objects.get_for_model(ICookIngredientModel)
    models = models.exclude(content_type__id=content_type.id)
    if models.count() == 0:
        return None
    elif models.count() >= 1:
        synonym = models[0]
        return synonym.content_object.nutrition


def find_similar_nutrition_model(name: str):
    nutrition = find_in_i_cook_ingredient_model(name)
    if nutrition:
        return nutrition

    nutrition = find_in_synonym_model(name)
    if nutrition:
        return nutrition

    return None


def find_by_same_gram(name, gram):
    if ICookIngredientModel.objects.is_in_db_already(name, gram):
        return ICookIngredientModel.objects.get(name=name, gram=gram)


def calculate_ingredient_nutrition(ingredient: Ingredient, similar_nutrition_model: NutritionModel) -> NutritionTuple:
    name = ingredient.name
    ratio = ingredient.gram / similar_nutrition_model.gram
    gram = ingredient.gram
    calories = similar_nutrition_model.calories * ratio
    protein = similar_nutrition_model.protein * ratio
    fat = similar_nutrition_model.fat * ratio
    carbohydrates = similar_nutrition_model.carbohydrates * ratio
    fruit_amount = similar_nutrition_model.fruit_amount * ratio
    vegetable_amount = similar_nutrition_model.vegetable_amount * ratio
    grain_amount = similar_nutrition_model.grain_amount * ratio
    protein_food_amount = similar_nutrition_model.protein_food_amount * ratio
    diary_amount = similar_nutrition_model.diary_amount * ratio
    oil_amount = similar_nutrition_model.oil_amount * ratio
    nutrition = NutritionTuple(name=name, gram=gram, calories=calories, protein=protein, fat=fat,
                               carbohydrates=carbohydrates,
                               fruit_amount=fruit_amount,
                               vegetable_amount=vegetable_amount,
                               grain_amount=grain_amount,
                               protein_food_amount=protein_food_amount,
                               diary_amount=diary_amount,
                               oil_amount=oil_amount)
    return nutrition


def create_ingredient_model(ingredient: Ingredient, nutrition: NutritionTuple):
    source = "ICook"
    nutrition_model = NutritionModel.objects.create(**nutrition._asdict())
    ingredient_model = ICookIngredientModel.objects.create(name=ingredient.name,
                                                           gram=ingredient.gram,
                                                           calories=nutrition.calories,
                                                           protein=nutrition.protein,
                                                           fat=nutrition.fat,
                                                           carbohydrates=nutrition.carbohydrates,
                                                           source=source,
                                                           nutrition=nutrition_model)
    ingredient_model.synonyms.create(synonym=ingredient.name)


def calculate_dish_nutrition(dish_name: str, nutrition_list: List[NutritionTuple]) -> NutritionTuple:
    gram = 0.0
    calories = 0.0
    protein = 0.0
    fat = 0.0
    carbohydrates = 0.0
    fruit_amount = 0.0
    vegetable_amount = 0.0
    grain_amount = 0.0
    protein_food_amount = 0.0
    diary_amount = 0.0
    oil_amount = 0.0

    name = dish_name

    for nutrition in nutrition_list:
        gram += nutrition.gram
        calories += nutrition.calories
        protein += nutrition.protein
        fat += nutrition.fat
        carbohydrates += nutrition.carbohydrates
        fruit_amount += nutrition.fruit_amount
        vegetable_amount += nutrition.vegetable_amount
        grain_amount += nutrition.grain_amount
        protein_food_amount += nutrition.protein_food_amount
        diary_amount += nutrition.diary_amount
        oil_amount += nutrition.oil_amount

    nutrition = NutritionTuple(name=name, gram=gram, calories=calories, protein=protein, fat=fat,
                               carbohydrates=carbohydrates,
                               fruit_amount=fruit_amount,
                               vegetable_amount=vegetable_amount,
                               grain_amount=grain_amount,
                               protein_food_amount=protein_food_amount,
                               diary_amount=diary_amount,
                               oil_amount=oil_amount)
    return nutrition


def create_nutrition_model(nutrition) -> NutritionModel:
    if nutrition.functions().is_valid():
        nutrition_model = NutritionModel.objects.create(**nutrition._asdict())
        nutrition_model.make_calories_image()
        if nutrition_model.is_six_group_valid():
            nutrition_model.make_six_group_image()
        nutrition_model.save()
        return nutrition_model
    else:
        raise ValueError('nutrition is not valid \n {}'.format(nutrition))


def try_add_relation_to_dish_ingredient_model(dish: Dish, dish_model: ICookDishModel):
    if not dish_model.icookdishingredientmodel_set.filter(dish=dish_model).count():
        for ingredient in dish.ingredients:
            dish_model.icookdishingredientmodel_set.create(name=ingredient.name,
                                                           gram=ingredient.gram)
        dish_model.save()


def try_add_dish_name_to_synonym_model(dish_model: ICookDishModel):
    if not dish_model.synonyms.count():
        dish_model.synonyms.create(synonym=dish_model.name)


def try_make_img(dish_model: ICookDishModel):
    nutrition = dish_model.nutrition
    if not nutrition.is_calories_image_created():
        nutrition.make_calories_image()
    if not nutrition.is_six_group_image_created():
        nutrition.make_six_group_image()
    nutrition.save()


def create_i_cook_dish_model(dish: Dish, nutrition_list: List[NutritionTuple]):
    status = False
    if ICookDishModel.objects.is_in_db_already(dish.source_url):
        dish_model = ICookDishModel.objects.get(source_url=dish.source_url)
    else:
        count_word = '一份'
        nutrition = calculate_dish_nutrition(dish.name, nutrition_list)
        nutrition_model = create_nutrition_model(nutrition)
        dish_model = ICookDishModel.objects.create(name=dish.name,
                                                   source_url=dish.source_url,
                                                   count_word=count_word,
                                                   nutrition=nutrition_model)
        status = True

    try_make_img(dish_model)
    try_add_relation_to_dish_ingredient_model(dish, dish_model)
    try_add_dish_name_to_synonym_model(dish_model)

    return status


def get_nutrition_list_from_ingredients(ingredients: List[Ingredient]) -> Optional[List[NutritionTuple]]:
    nutrition_list = []
    for ingredient in ingredients:
        print('ingredient: %s' % ingredient.name)
        nutrition_model = find_similar_nutrition_model(ingredient.name)
        if not nutrition_model:
            print('Lack of {}, skip this dish'.format(ingredient.name))
            return None
        nutrition = calculate_ingredient_nutrition(ingredient, nutrition_model)
        nutrition_list.append(nutrition)
    return nutrition_list


def run():
    raw_dishes = read_dishes()

    counts = 0
    for raw_dish in raw_dishes:
        ingredients = [Ingredient(**i) for i in raw_dish['ingredients']]
        dish = Dish(**raw_dish)
        dish = dish._replace(ingredients=ingredients)

        print('Dish: %s' % dish.name)

        nutrition_list = get_nutrition_list_from_ingredients(dish.ingredients)
        if not nutrition_list:
            continue

        status = create_i_cook_dish_model(dish, nutrition_list)
        if not status:
            print()
            print(dish)
            print('already exist')
            print()
        else:
            counts += 1
    print('End with: {} added.'.format(counts))
