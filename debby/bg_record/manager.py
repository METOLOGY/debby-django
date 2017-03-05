from typing import Dict

from linebot import LineBotApi
from linebot.models import ConfirmTemplate
from linebot.models import MessageEvent
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from .models import BGModel
from user.models import CustomUserModel


class BGRecordManager:
    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text='嗨，現在要記錄血糖嗎？',
            actions=[
                PostbackTemplateAction(
                    label='好啊',
                    data='action=record_bg&choice=true'
                ),
                PostbackTemplateAction(
                    label='等等再說',
                    data='action=record_bg&choice=false'
                )
            ]
        )
    )

    #
    # def __init__(self, line_bot_api: LineBotApi, event: MessageEvent):
    #     self.line_bot_api = line_bot_api
    #     self.event = event

    # def ask_if_want_to_record_bg(self):
    #     self._reply_message(self.confirm_template_message)

    def reply_does_user_want_to_record(self):
        return self.confirm_template_message

    def reply_to_input(self, query_string: Dict[str, list]):
        message = ''
        if query_string['choice'][0] == 'true':
            message = '那麼，輸入血糖～'
        elif query_string['choice'][0] == 'false':
            message = '好，要隨時注意自己的血糖狀況哦！'
        send_message = TextSendMessage(text=message)

        self._reply_message(send_message)

    @staticmethod
    def record_bg_record(current_user: CustomUserModel, bg_value: int):
        bg = BGModel(user=current_user, glucose_val=bg_value)
        bg.save()

    def reply_record_success(self):
        send_message = TextSendMessage(text='紀錄成功！')
        self._reply_message(send_message)

    def _reply_message(self, send_message: SendMessage):
        self.line_bot_api.reply_message(
            self.event.reply_token,
            send_message)

    def record_reminder(self):
        total_members_line_id = [x.line_id for x in CustomUserModel.objects.all() if len(x.line_id) == 33]
        print(total_members_line_id)

        for member in total_members_line_id:
            self.line_bot_api.push_message(member, self.confirm_template_message)
