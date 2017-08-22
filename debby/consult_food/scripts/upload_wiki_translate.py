import csv
from consult_food.models import WikiFoodTranslateModel

def run():
    WikiFoodTranslateModel.objects.all().delete()

    with open('../chat_table/cuisine_zh.csv') as csvfile:
        for line in csv.reader(csvfile):
            [ori, trans] = line
            model = WikiFoodTranslateModel(english=ori, chinese=trans)
            model.save()