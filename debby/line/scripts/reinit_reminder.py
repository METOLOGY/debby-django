from user.models import CustomUserModel
from reminder.models import UserReminder
import datetime

for user in CustomUserModel.objects.all():
    if len(user.line_id) == 33:
        for reminder_type in ['bg', 'insulin', 'drug']:
            for time in [datetime.time(7, 0), datetime.time(8, 0), datetime.time(12, 0), datetime.time(18, 0), datetime.time(22, 0)]:
                if time == datetime.time(8, 0) and reminder_type == 'drug':
                    UserReminder.objects.get_or_create(user=user, type=reminder_type, time=time, status=True)
                else:
                    UserReminder.objects.get_or_create(user=user, type=reminder_type, time=time, status=False)
