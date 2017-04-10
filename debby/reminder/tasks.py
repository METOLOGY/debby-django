from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_celery_beat.models import PeriodicTask, PeriodicTasks, CrontabSchedule, IntervalSchedule
from datetime import time
import json


from bg_record.manager import BGRecordManager
from debby.settings import LINE_BOT_API
from user.models import CustomUserModel


@shared_task
def record_bg_reminder(line_id):
    # BGRecordManager.record_reminder(LINE_BOT_API, line_id=line_id)
    print(line_id)

@shared_task
def periodic_checking_bg_reminder_setting():
    for user in CustomUserModel.objects.all():
        if len(user.line_id) == 33:
            try:

                interval, _ = IntervalSchedule.objects.get_or_create(every='3', period='seconds')

                # breakfast
                breakfast_reminder = user.usersettingmodel_set.last().breakfast_reminder # TYPE: datatime.time
                breakfast_schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=breakfast_reminder.minute,
                    hour=breakfast_reminder.hour
                )
                breakfast, _ = PeriodicTask.objects.get_or_create(
                    name=user.line_id + '_breakfast',
                )

                # if time changed, than recreat
                if breakfast.crontab != breakfast_schedule or breakfast.crontab == None:
                    # breakfast.crontab = breakfast_schedule
                    breakfast.interval = interval
                    breakfast.task = 'line.tasks.record_bg_reminder'
                    breakfast.args = json.dumps([user.line_id])
                    breakfast.enabled = True
                    breakfast.save()
                    print('breakfast changed')
                    PeriodicTasks.changed(breakfast)


                # lunch
                lunch_reminder = user.usersettingmodel_set.last().lunch_reminder
                lunch_schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=lunch_reminder.minute,
                    hour=lunch_reminder.hour
                )

                lunch, _ = PeriodicTask.objects.get_or_create(
                    name=user.line_id + '_lunch',
                )

                if lunch.crontab != lunch_schedule or lunch.crontab == None:
                    lunch.crontab = lunch_schedule
                    lunch.task = 'line.tasks.record_bg_reminder'
                    lunch.args = json.dumps([user.line_id])
                    lunch.enabled = True
                    lunch.save()
                    print('lunch changed')
                    PeriodicTasks.changed(lunch)


                # dinner
                dinner_reminder = user.usersettingmodel_set.last().dinner_reminder
                dinner_schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=dinner_reminder.minute,
                    hour=dinner_reminder.hour
                )

                dinner, _ = PeriodicTask.objects.get_or_create(
                    name=user.line_id + '_dinner',
                )
                if dinner.crontab != dinner_schedule or dinner.crontab == None:
                    dinner.crontab = dinner_schedule
                    dinner.task = 'line.tasks.record_bg_reminder'
                    dinner.args = json.dumps([user.line_id])
                    dinner.enabled = True
                    dinner.save()
                    print('dinner changed')
                    PeriodicTasks.changed(dinner)

                # PeriodicTasks.changed()

            except PeriodicTask.DoesNotExist as e:
                print(e)
