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
    def reply_does_user_want_to_record(self) -> TemplateSendMessage:
        return TemplateSendMessage(
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

    @staticmethod
    def reply_record_success() -> TextSendMessage:
        return TextSendMessage(text='紀錄成功！')

    @staticmethod
    def reply_to_user_choice(data) -> TextSendMessage:
        message = ''
        choice = data['choice']
        if choice == 'true':
            message = '那麼，輸入血糖～'
        elif choice == 'false':
            message = '好，要隨時注意自己的血糖狀況哦！'

        return TextSendMessage(text=message)

    # def record_reminder(self):
    #     total_members_line_id = [x.line_id for x in CustomUserModel.objects.all() if len(x.line_id) == 33]
    #     print(total_members_line_id)
    #
    #     for member in total_members_line_id:
    #         self.line_bot_api.push_message(member, self.confirm_template_message)

    @staticmethod
    def record_bg_record(current_user: CustomUserModel, bg_value: int):
        bg = BGModel(user=current_user, glucose_val=bg_value)
        bg.save()
