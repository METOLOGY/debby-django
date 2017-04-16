from django.core.cache import cache
from django.conf import settings
from line.callback import ReminderCallback
from linebot.models import SendMessage, TextSendMessage, ButtonsTemplate, PostbackTemplateAction, TemplateSendMessage
from user.cache import AppCache
from django_celery_beat.models import PeriodicTask
from reminder.models import UserReminder

from line.callback import BGRecordCallback
from bg_record.manager import BGRecordManager
from user.cache import ReminderData


class ReminderManager(object):
    def __init__(self, callback: ReminderCallback):
        self.callback = callback

    @staticmethod
    def reply_reminder(line_id: str, reminder_id: int):
        """
        :param line_id: a true line ID.
        :param type: reminder type.

        This function is designed for celery beat task.
        """
        assert len(line_id) == 33 # check line_id is a true line ID
        reminder = UserReminder.objects.get(id=reminder_id)
        type = reminder.type

        if type == 'bg':
            reminder_text = 'Debby提醒您: 請記得量血糖喔～'
        elif type == 'insulin':
            reminder_text = 'Debby提醒您: 請記得注射胰島素喔～'
        elif type == 'drug':
             reminder_text = 'Debby提醒您：請記得服用藥物哦～'


        reminder_message = TemplateSendMessage(
            alt_text='使用者回覆',
            template=ButtonsTemplate(
                text=reminder_text,
                actions=[
                    PostbackTemplateAction(
                        label='好的',
                        data='app=Reminder&action=REPLY_REMINDER&choice=1&reminder_id={}'.format(reminder.id),
                    ),
                    PostbackTemplateAction(
                        label='關閉此次提醒',
                        data='app=Reminder&action=REPLY_REMINDER&choice=2&reminder_id={}'.format(reminder.id),
                    ),
                    PostbackTemplateAction(
                        label='10分鐘後再提醒我',
                        data='app=Reminder&action=REPLY_REMINDER&choice=3&reminder_id={}'.format(reminder.id),
                    ),
                ]
            )
        )

        line_bot_api = settings.LINE_BOT_API
        print(line_id)
        line_bot_api.push_message(to=line_id, messages=reminder_message)


    def reply_reminder_awaits(self):
        return [
            TextSendMessage(text='10分鐘後Debby會再次提醒您量血糖'),
            TextSendMessage(text='您可至"我的設定"中調整提醒時間')
            ]

    @staticmethod
    def reply_next_reminder(reminder: UserReminder):
        type_zh = ''
        time = reminder.time
        type = reminder.type
        if type == 'bg':
            type_zh = '血糖'
        elif type == 'insulin':
            type_zh = '胰島素'
        elif type == 'drug':
            type_zh = '藥物'

        return [
            TextSendMessage(text='下一次量測{}提醒時間是: {})'.format(type_zh, time)),
            TextSendMessage(text='您可至"我的設定"中調整提醒時間')
            ]


    def reply_no_next_reminder(self):
        return [
            TextSendMessage(text='您今日已沒有下一次的提醒項目!'),
            TextSendMessage(text='您可至"我的設定"中調整提醒時間')
            ]

    @staticmethod
    def find_next_reminder(reminder: UserReminder):
        reminders = UserReminder.objects.filter(user=reminder.user, type=reminder.type)
        time = []
        for re in reminders:
            time.append(re.time)
        time = sorted(time)
        index = time.index(reminder.time)
        try:
            return UserReminder.objects.get(user=reminder.user, type=reminder.type, time=time[index+1])
        except:
            # return UserReminder.objects.get(user=reminder.user, type=reminder.type, time=time[0])
            return None

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR')
        app_cache = AppCache(self.callback.line_id, app='Reminder')

        print(self.callback.action, self.callback.choice, self.callback.reminder_id)
        if self.callback.action == 'REPLY_REMINDER':
            choice = int(self.callback.choice)
            if choice == 1:
                data = ReminderData()
                data.reminder_id = self.callback.reminder_id
                app_cache.data = data
                app_cache.commit()

                _callback = BGRecordCallback(line_id=self.callback.line_id,action='CREATE_FROM_MENU', text='血糖紀錄')

                print(_callback.text, _callback.app, _callback.action)
                reply = BGRecordManager(_callback).handle()


            elif choice == 2:
                reminder = UserReminder.objects.get(id=self.callback.reminder_id)
                next_reminder = self.find_next_reminder(reminder)
                if next_reminder != None:
                    print(reminder)
                    reply = self.reply_next_reminder(reminder=next_reminder)
                else:
                    reply = self.reply_no_next_reminder()

            elif choice == 3:
                reminder = UserReminder.objects.get(id=self.callback.reminder_id)
                reminder.time = reminder.time.replace(minute=reminder.time.minute + 10)
                reminder.save()
                reply = self.reply_reminder_awaits()
            else:
                print(self.callback.choice)


        return reply