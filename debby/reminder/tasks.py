from __future__ import absolute_import, unicode_literals

import json
import pytz
from datetime import datetime, timedelta
from django_q.models import Schedule

from reminder.manager import ReminderManager
from reminder.models import UserReminder


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
    fake_time = datetime.combine(datetime.now(), reminder.time).astimezone(tz)
    fake_time_plus_2 = fake_time + timedelta(minutes=2)
    time_now = datetime.now().astimezone(tz).time()

    if reminder.status:
        if fake_time.time() <= time_now  <= fake_time_plus_2.time():
            print('----{}---- reminder sent to {}: {} ----{}---'.format(fake_time.time(),line_id, time_now, fake_time_plus_2.time()))
            ReminderManager.reply_reminder(line_id=line_id, reminder_id=reminder_id)


def periodic_checking_bg_reminder_setting():
    """
    check user personal reminder settings and update schedule tasks by minutes.

    :return:
    """

    reminders = UserReminder.objects.all()
    for num, reminder in enumerate(reminders):
        sch, created = Schedule.objects.get_or_create(
            name=reminder.user.line_id + '_reminder_' + str(num),
        )

        if created:
            sch.func = 'reminder.tasks.record_reminder'
            sch.args = json.dumps([reminder.user.line_id, reminder.id])
            sch.schedule_type = Schedule.DAILY
            sch.repeats = -1
            sch.next_run = datetime.combine(datetime.now(), reminder.time).astimezone(tz)
            sch.save()
            print('created')
        else:
            if sch.next_run.astimezone(tz).time() != reminder.time:
                sch.next_run = datetime.combine(datetime.now(), reminder.time).astimezone(tz)
                sch.save()
                print('reminder time changed: {}'.format(sch.id))
            else:
                pass
