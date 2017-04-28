from line.models import EventModel

obj, created = EventModel.objects.get_or_create(phrase="我的日記", callback="MyDiary", action="START")
obj, created = EventModel.objects.get_or_create(phrase="我的設定", callback="UserSetting", action="CREATE_FROM_MENU")

print(obj, created)
