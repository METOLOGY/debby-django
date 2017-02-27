from io import BytesIO

from django.core.files import File
from linebot import LineBotApi
from linebot.models import MessageEvent
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
