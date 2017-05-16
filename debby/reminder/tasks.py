from __future__ import absolute_import, unicode_literals

import json
import pytz
from datetime import datetime
from django_q.models import Schedule

from reminder.manager import ReminderManager
from reminder.models import UserReminder
from user.models import CustomUserModel

tz = pytz.timezone('Asia/Taipei')


def record_reminder(data):
    """
    determine reminder message should be sent or not

    :param data:
    :return:
    """
    line_id = data[0]
    reminder_id = data[1]
    reminder = UserReminder.objects.get(id=reminder_id)
    time_now = datetime.now().astimezone(tz).time()

    if reminder.status and time_now.hour == reminder.time.hour and time_now.minute == reminder.time.minute:
        ReminderManager.reply_reminder(line_id=line_id, reminder_id=reminder_id)


def periodic_checking_bg_reminder_setting():
    """
    check user personal reminder settings and update schedule tasks by minutes.

    :return:
    """
    for user in CustomUserModel.objects.all():
        if len(user.line_id) == 33:
            reminders = UserReminder.objects.filter(user=user)

            for num, reminder in enumerate(reminders):
                sch, created = Schedule.objects.get_or_create(
                    name=user.line_id + '_reminder_' + str(num),
                )

                sch.func = 'reminder.tasks.record_reminder'
                sch.args = json.dumps([user.line_id, reminder.id])
                sch.schedule_type = Schedule.DAILY
                sch.repeats = -1
                set_time = reminder.time
                sch.next_run = datetime.today().astimezone(tz).replace(hour=set_time.hour, minute=set_time.minute)
                sch.save()
