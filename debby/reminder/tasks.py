from __future__ import absolute_import, unicode_literals

import json
import arrow
import pytz
from django_q.models import Schedule

from reminder.manager import ReminderManager
from reminder.models import UserReminder
from user.models import CustomUserModel

tz = pytz.timezone('Asia/Taipei')


def record_reminder(data):
    line_id = data[0]
    reminder_id = data[1]
    reminder = UserReminder.objects.get(id=reminder_id)
    if reminder.status:
        ReminderManager.reply_reminder(line_id=line_id, reminder_id=reminder_id)


def periodic_checking_bg_reminder_setting():
    for user in CustomUserModel.objects.all():
        if len(user.line_id) == 33:
            reminders = UserReminder.objects.filter(user=user)

            for num, reminder in enumerate(reminders):

                sch, _ = Schedule.objects.get_or_create(
                    name=user.line_id + '_reminder_' + str(num),
                )

                sch_ori_time = sch.next_run.astimezone(tz=tz)

                if sch.repeats == 1 or sch.repeats == -1:
                    sch_status = True
                else:
                    sch_status = False

                if (sch_ori_time.hour != reminder.time.hour and sch_ori_time.minute != reminder.time.minute) or sch_status != reminder.status:
                    print(sch_ori_time)
                    print(reminder.time)
                    print((sch_ori_time.hour != reminder.time.hour and sch_ori_time.minute != reminder.time.minute))
                    print(sch_status != reminder.status)
                    sch.func = 'reminder.tasks.record_reminder'
                    sch.args = json.dumps([user.line_id, reminder.id])

                    if reminder.status:
                        sch.repeats = 1  # always turn on
                    else:
                        sch.repeats = 0  # turn off

                    sch_time = arrow.utcnow().to('Asia/Taipei').replace(
                        hour=reminder.time.hour, minute=reminder.time.minute
                    )
                    sch.next_run = str(sch_time)
                    sch.schedule_type = Schedule.DAILY
                    print('save')
                    sch.save()
