from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_celery_beat.models import PeriodicTask, PeriodicTasks, CrontabSchedule, IntervalSchedule

from user.models import CustomUserModel
from reminder.models import UserReminder
from reminder.manager import ReminderManager

import json

@shared_task
def record_bg_reminder(line_id):
    # BGRecordManager.record_reminder(LINE_BOT_API, line_id=line_id)
    print(line_id)


@shared_task
def record_reminder(line_id: str, reminder_type: str):
    ReminderManager.reply_reminder(line_id=line_id, type=reminder_type)

@shared_task
def periodic_checking_bg_reminder_setting():
    for user in CustomUserModel.objects.all():
        if len(user.line_id) == 33:
            try:
                # update the reminder crontab tasks with user reminder model

                reminders = UserReminder.objects.filter(user=user)
                for num, reminder in enumerate(reminders):
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=reminder.time.minute,
                        hour=reminder.time.hour,
                    )

                    reminder_task, _ = PeriodicTask.objects.get_or_create(
                        name=user.line_id + '_reminder_' + str(num),
                    )

                    reminder_task.crontab = schedule
                    reminder_task.task = 'reminder.tasks.record_reminder'
                    reminder_task.args = json.dumps([user.line_id, reminder.type])
                    reminder_task.enabled = True
                    reminder_task.save()


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

            except PeriodicTask.DoesNotExist as e:
                print(e)
