from line.models import EventModel

obj, created = EventModel.objects.get_or_create(phrase="我的日記", callback="MyDiary", action="START")

print(obj, created)
