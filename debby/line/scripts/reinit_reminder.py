from user.models import CustomUserModel
from reminder.models import UserReminder
from datetime import datetime

for user in CustomUserModel.objects.all():
    for reminder_type in ['bg', 'insulin', 'drug']:
        for time in [datetime.time(7, 00), datetime.time(8, 00), datetime.time(12, 00), datetime.time(18, 00), datetime.time(22, 00)]:
            UserReminder.objects.get_or_create(user=user, type=reminder_type, time=time, status=False)
