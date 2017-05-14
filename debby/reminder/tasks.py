from __future__ import absolute_import, unicode_literals

import json

#from celery import shared_task
#from django_celery_beat.models import PeriodicTask, CrontabSchedule

from django_q.models import Schedule

from reminder.manager import ReminderManager
from reminder.models import UserReminder
from user.models import CustomUserModel

def record_reminder(line_id: str, reminder_id: int, **kwargs):
    line_id = kwargs['line_id']
    reminder_id = kwargs['reminder_id']
    ReminderManager.reply_reminder(line_id=line_id, reminder_id=reminder_id)


def periodic_checking_bg_reminder_setting():
    for user in CustomUserModel.objects.all():
        if len(user.line_id) == 33:
            # try:
                # update the reminder crontab tasks with user reminder model

            reminders = UserReminder.objects.filter(user=user)
            for num, reminder in enumerate(reminders):



                sch, _ = Schedule.objects.get_or_create(
                    name=user.line_id + '_reminder_' + str(num),
                )

                sch.task = 'reminder.task.record_reminder'
                sch.args = {
                    'line_id': user.line_id,
                    'reminder_id': 'reminder.id'
                }

                sch.next_run = reminder.time
                sch.schedule_type = Schedule.DAILY
                sch.save()

                    # schedule, _ = CrontabSchedule.objects.get_or_create(
                    #     minute=reminder.time.minute,
                    #     hour=reminder.time.hour,
                    # )
                    #
                    # reminder_task, _ = PeriodicTask.objects.get_or_create(
                    #     name=user.line_id + '_reminder_' + str(num),
                    # )
                    #
                    # reminder_task.crontab = schedule
                    # reminder_task.task = 'reminder.tasks.record_reminder'
                    # reminder_task.args = json.dumps([user.line_id, reminder.id])
                    # reminder_task.enabled = True
                    # reminder_task.save()


                    # breakfast_reminder = user.usersettingmodel_set.last().breakfast_reminder # TYPE: datatime.time
                    # breakfast_schedule, _ = CrontabSchedule.objects.get_or_create(
                    #     minute=breakfast_reminder.minute,
                    #     hour=breakfast_reminder.hour
                    # )
                    # breakfast, _ = PeriodicTask.objects.get_or_create(
                    #     name=user.line_id + '_breakfast',
                    # )
                    #
                    # # if time changed, than recreat
                    # if breakfast.crontab != breakfast_schedule or breakfast.crontab == None:
                    #     breakfast.crontab = breakfast_schedule
                    #     # breakfast.interval = interval
                    #     breakfast.task = 'line.tasks.record_bg_reminder'
                    #     breakfast.args = json.dumps([user.line_id])
                    #     breakfast.enabled = True
                    #     breakfast.save()
                    #     print('breakfast changed')
                    #     PeriodicTasks.changed(breakfast)


                    # PeriodicTasks.changed()

            # except PeriodicTask.DoesNotExist as e:
            #     print(e)
