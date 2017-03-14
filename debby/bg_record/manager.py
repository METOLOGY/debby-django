from linebot.models import ConfirmTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from line.callback import BGRecordCallback
from .models import BGModel
from user.models import CustomUserModel


class BGRecordManager:
    line_id = ''
    confirm_template_message = TemplateSendMessage(
        alt_text='嗨，現在要記錄血糖嗎？',
        template=ConfirmTemplate(
            text='嗨，現在要記錄血糖嗎？',
            actions=[
                PostbackTemplateAction(
                    label='好啊',
                    data=BGRecordCallback(line_id=line_id,
                                          action='CREATE',
                                          choice='true').url
                ),
                PostbackTemplateAction(
                    label='等等再說',
                    data=BGRecordCallback(line_id=line_id,
                                          action='CREATE',
                                          choice='false').url
                )
            ]
        )
    )

    def __init__(self, callback: BGRecordCallback):
        self.callback = callback

    def reply_does_user_want_to_record(self) -> TemplateSendMessage:
        return self.confirm_template_message

    @staticmethod
    def reply_record_success() -> TextSendMessage:
        return TextSendMessage(text='紀錄成功！')

    def reply_to_user_choice(self) -> TextSendMessage:
        message = ''
        choice = self.callback.choice
        if choice == 'true':
            message = '那麼，輸入血糖～'
        elif choice == 'false':
            message = '好，要隨時注意自己的血糖狀況哦！'

        return TextSendMessage(text=message)

    def record_reminder(self, line_bot_api):
        total_members_line_id = [x.line_id for x in CustomUserModel.objects.all() if len(x.line_id) == 33]
        print(total_members_line_id)

        for member in total_members_line_id:
            line_bot_api.push_message(member, self.confirm_template_message)

    @staticmethod
    def record_bg_record(current_user: CustomUserModel, bg_value: int):
        bg = BGModel(user=current_user, glucose_val=bg_value)
        bg.save()

    def handle(self):
        if self.callback.action == 'CREATE':
            return self.reply_to_user_choice()
