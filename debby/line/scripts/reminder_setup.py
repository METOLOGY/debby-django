from django_q.models import Schedule

# init the userSetting checking schedule
Schedule.objects.get_or_create(func='reminder.tasks.periodic_checking_bg_reminder_setting',
                               name='check-user-remnder-setting',
                               schedule_type=Schedule.MINUTES,
                               minutes=1,
                               repeats=-1,
                               )
