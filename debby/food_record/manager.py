from io import BytesIO

from django.core.files import File
from linebot import LineBotApi
from linebot.models import ConfirmTemplate
from linebot.models import MessageEvent
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models.responses import MessageContent

from food_record.models import FoodModel
from user.models import CustomUserModel


class FoodRecordManager:
    def __init__(self, line_bot_api: LineBotApi, event: MessageEvent):
        self.line_bot_api = line_bot_api
        self.event = event

    @staticmethod
    def record_image(current_user: CustomUserModel, image_content: MessageContent):
        food_record = FoodModel()
        io = BytesIO(image_content)
        food_record.food_image_upload.save('{0}_food_image.jpg'.format(current_user.line_id), File(io))

    def _reply_message(self, send_message: SendMessage):
        self.line_bot_api.reply_message(
            self.event.reply_token,
            send_message)

    def ask_if_want_to_record_food(self):
        self._reply_message(TemplateSendMessage(
            alt_text='Do you want to record food?',
            template=ConfirmTemplate(
                text='請問是否要記錄飲食',
                actions=[
                    PostbackTemplateAction(
                        label='好喔',
                        data='action=food_record&choice=true'
                    ),
                    PostbackTemplateAction(
                        label='等等再說',
                        data='action=food_record&choice=true'
                    )
                ]
            )
        ))
