from django.core.cache import cache
from django.conf import settings
from line.callback import ReminderCallback
from linebot.models import SendMessage
from linebot.models import TextSendMessage
from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction
from user.cache import AppCache
from .models import UserReminder


class ReminderManager(object):
    def __init__(self, callback: ReminderCallback):
        self.callback = callback

    @staticmethod
    def reply_reminder(line_id: str, type: str):
        """
        :param line_id: a true line ID.
        :param type: reminder type.

        This function is designed for celery beat task.
        """
        assert len(line_id) == 33 # check line_id is a true line ID

        if type == 'bg':
            reminder_text = 'Debby提醒您: 請記得量血糖喔～'
        elif type == 'insulin':
            reminder_text = 'Debby提醒您: 請記得注射胰島素喔～'
        elif type == 'drug':
             reminder_text = 'Debby提醒您：請記得服用藥物哦～'


        reminder_message = TextSendMessage(
            alt_text='使用者回覆',
            template=ButtonsTemplate(
                type='buttons',
                text=reminder_text,
                title=reminder_text,
                actions=[
                    PostbackTemplateAction(
                        label='好的',
                        text='好的',
                        data='app=BGRecord&action=CREATE_FROM_MENU',
                    ),
                    PostbackTemplateAction(
                        label='關閉此次提醒',
                        text='關閉此次提醒',
                        data='app=Reminder&action=REPLY_REMINDER&choice=2',
                    ),
                    PostbackTemplateAction(
                        label='10分鐘後再提醒我',
                        text='10分鐘後再提醒我',
                        data='app=Reminder&action=REPLY_REMINDER&choice=3',
                    ),
                ]
            )
        )

        line_bot_api = settings.LINE_BOT_API
        line_bot_api.push_message(line_id, messages=reminder_message)


    def reply_reminder_awaits(self):
        return TextSendMessage(text='10分鐘後Debby會再次提醒您量血糖; 您可至"我的設定"中調整提醒時間')

    def reply_next_reminder(self, type:str, reminder_time='19:00'):
        type_zh = ''
        if type == 'bg':
            type_zh = '血糖'
        elif type == 'insulin':
            type_zh = '胰島素'
        elif type == 'drug':
            type_zh = '藥物'

        return TextSendMessage(
            text='下一次量測{}提醒時間是: {} 您可至"我的設定"中調整提醒時間'.format(type_zh, reminder_time)
        )


    def reply_no_next_reminder(self):
        return TextSendMessage(text='您沒有下一次的提醒項目 您可至"我的設定"中調整提醒時間')


    def handler(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR')
        app_cache = AppCache(self.callback.line_id, app='Reminder')

        if self.callback.action == 'REPLY_REMINDER':
            if self.callback.choice == 2:
                pass
            elif self.callback.choice == 3:
                pass
