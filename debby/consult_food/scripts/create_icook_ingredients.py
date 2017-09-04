from typing import Dict, Union

from consult_food.models import TaiwanSnackModel, TFDAModel, ICookIngredientModel
from debby.utils import load_from_json_file


def is_name_exist(name: str):
    orders = [
        TaiwanSnackModel.objects.search_by_name,
        TaiwanSnackModel.objects.search_by_synonyms,
        TFDAModel.objects.search_by_name,
        TFDAModel.objects.search_by_synonyms
    ]

    for order in orders:
        queries = order(name)
        if len(queries) >= 1:
            return True
    return False


def run():
    data = load_from_json_file('../chat_table/ingredient_ref_fda.json')  # type: Dict[Union[Dict, str]]
    for name in data.keys():
        if ICookIngredientModel.objects.search_by_name(name):
            continue
        elif is_name_exist(name):
            continue
        else:
            print("ingredient: ", name)
            fda_name = data[name]['fda_name']
            queries = TFDAModel.objects.filter(sample_name=fda_name)
            if len(queries) > 1:
                for q in queries:
                    print(q.sample_name)
                raise ValueError("too many food result")
            elif len(queries) == 0:
                print("fda name: ", fda_name)
                raise ValueError("no food result")
            else:
                print("fda name: ", fda_name)
                fda_food = queries[0]
                icook = ICookIngredientModel.objects.get_or_create(name=name, nutrition=fda_food.nutrition, source="TFDA")
                icook.synonyms.create(synonym=name)
