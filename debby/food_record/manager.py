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

    def delete_cache(self):
        user_cache = cache.get(self.callback.line_id)
        if user_cache:
            cache.delete(self.callback.line_id)

    def let_cache_record(self, key: str, value, time: int = 60):
        """
        Keep status in cache, identify user by line_id
        :param key: key in cache, must in str
        :param value: value in cache
        :param time: hold the cache in x seconds.
        :return: None
        """
        user_cache = cache.get(self.callback.line_id)
        if not user_cache:
            user_cache = {key: value}
        else:
            user_cache[key] = value
        cache.set(self.callback.line_id, user_cache, time)

    def handle(self) -> SendMessage:
        if self.callback.action == 'CREATE':
            current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            food_record_pk = self.record_image(current_user, self.image_content)
            self.let_cache_record(key='food_record_pk', value=food_record_pk, time=120)
            print('in\n')
            return self.reply_to_record_detail_template()

        elif self.callback.action == 'CREATE_FROM_MENU':
            return TextSendMessage(text='請上傳一張此次用餐食物的照片,或輸入文字: ')

        elif self.callback.action == 'UPDATE':
            user_cache = cache.get(self.callback.line_id)
            if user_cache:
                if 'food_record_pk' in user_cache.keys():
                    if self.callback.text.upper() != 'N':
                        self.record_extra_info(user_cache['food_record_pk'], self.callback.text)
                        self.let_cache_record(key='KEEP_RECORDING', value=True, time=60)
                        message = self.reply_keep_recording()
                    else:
                        message = self.reply_record_success()
                        self.delete_cache()
                    return message

        elif self.callback.action == 'write_detail_notes':
            return self.reply_to_record_detail_template()
