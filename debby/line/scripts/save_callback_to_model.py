from line.models import EventModel

EventModel.objects.create(phrase='記錄飲食', callback='FoodRecord', action='CREATE')
EventModel.objects.create(phrase='記錄血糖', callback='BGRecord', action='CREATE')
EventModel.objects.create(phrase='食物查詢', callback='FoodQuery', action='READ')
EventModel.objects.create(phrase='藥物查詢', callback='DrugQuery', action='READ')
