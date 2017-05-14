from line.constant import App, MyDiaryAction
from line.models import EventModel

# from menu
EventModel.objects.get_or_create(phrase='飲食紀錄', callback='FoodRecord', action='CREATE_FROM_MENU')
EventModel.objects.get_or_create(phrase='血糖紀錄', callback='BGRecord', action='CREATE_FROM_MENU')
EventModel.objects.get_or_create(phrase='食物熱量查詢', callback='FoodQuery', action='READ')
EventModel.objects.get_or_create(phrase='藥物資訊查詢', callback='DrugQuery', action='READ')

EventModel.objects.get_or_create(phrase='血糖紀錄', callback='BGRecord', action='CREATE_FROM_MENU')
EventModel.objects.get_or_create(phrase='飲食紀錄', callback='FoodRecord', action='CREATE_FROM_MENU')
EventModel.objects.get_or_create(phrase='食物熱量查詢', callback='FoodQuery', action='READ_FROM_MENU')
EventModel.objects.get_or_create(phrase='藥物資訊查詢', callback='DrugQuery', action='READ_FROM_MENU')

EventModel.objects.get_or_create(phrase='我的日記', callback=App.MY_DIARY, action=MyDiaryAction.CREATE_FROM_MENU)
