from django.core.cache import cache
from line.callback import ReminderCallback
from linebot.models import SendMessage
from linebot.models import TextSendMessage
from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction


class ReminderManager():
    def __init__(self, callback: ReminderCallback):
        self.callback = callback

    def reply_reminder(self, type: str, reminder_time='12:00'):
        reminder_time = 'default reminder time'
        reminder_text = reminder_time
        if type == 'bg':
            reminder_text = 'Debby提醒您: 請記得量血糖喔～'
        elif type == 'insulin':
            reminder_text = 'Debby提醒您: 請記得注射胰島素喔～'
        elif type == 'drug':
             reminder_text = 'Debby提醒您：請記得服用藥物哦～'


        TextSendMessage(
            alt_text='使用者回覆',
            template=ButtonsTemplate(
                type='buttons',
                text=reminder_text,
                title=reminder_time,
                actions=[
                    PostbackTemplateAction(
                        label='好的',
                        text='好的',
                        data='app="reminder"&action=REPLY_REMINDER&choice=1',
                    ),
                    PostbackTemplateAction(
                        label='關閉此次提醒',
                        text='關閉此次提醒',
                        data='app="reminder"&action=REPLY_REMINDER&choice=2',
                    ),
                    PostbackTemplateAction(
                        label='10分鐘後再提醒我',
                        text='10分鐘後再提醒我',
                        data='app="reminder"&action=REPLY_REMINDER&choice=3',
                    ),
                ]
            )
        )

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
