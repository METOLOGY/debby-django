from io import BytesIO

from django.core.cache import cache
from django.core.files import File
from linebot.models import ConfirmTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from food_record.models import FoodModel
from line.callback import FoodRecordCallback
from user.cache import AppCache, FoodData
from user.models import CustomUserModel


class FoodRecordManager:
    def __init__(self, callback: FoodRecordCallback, image_content: bytes = bytes()):
        self.callback = callback
        self.image_content = image_content

    @staticmethod
    def record_image(current_user: CustomUserModel, image_content: bytes):
        food_record = FoodModel(user=current_user)
        io = BytesIO(image_content)

        file = '{0}_food_image.jpg'.format(current_user.line_id)
        food_record.food_image_upload.save(file, File(io))
        return food_record.pk

    @staticmethod
    def reply_to_record_detail_template():
        message = '您是否要繼續增加文字說明? (請輸入; 若已完成紀錄請回傳英文字母N )'
        return TextSendMessage(text=message)

    @staticmethod
    def reply_keep_recording():
        return TextSendMessage(text="繼續說")

    @staticmethod
    def reply_record_success():
        return TextSendMessage(text="記錄成功!")

    @staticmethod
    def record_extra_info(record_pk: str, text: str):
        food_record = FoodModel.objects.get(pk=record_pk)

        if food_record.note:
            food_record.note += "\n" + text
        else:
            food_record.note = text
        food_record.save()

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id)
        if self.callback.action == 'CREATE':
            current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            fd = FoodData()
            fd.food_record_pk = self.record_image(current_user, self.image_content)

            app_cache.save_data(app="FoodRecord", action="CREATE", data=fd)
            print('in\n')
            reply = self.reply_to_record_detail_template()

        elif self.callback.action == 'CREATE_FROM_MENU':
            reply = TextSendMessage(text='請上傳一張此次用餐食物的照片,或輸入文字: ')

        elif self.callback.action == 'UPDATE':
            if app_cache.is_app_running():
                data = app_cache.data  # type: FoodData
                if data.food_record_pk:
                    if self.callback.text.upper() != 'N':
                        self.record_extra_info(data.food_record_pk, self.callback.text)

                        # save to cache
                        data.keep_recording = True
                        app_cache.set_data(data)
                        app_cache.commit()

                        message = self.reply_keep_recording()
                    else:
                        message = self.reply_record_success()
                        app_cache.delete()
                    reply = message

        elif self.callback.action == 'write_detail_notes':
            reply = self.reply_to_record_detail_template()
            
        return reply
