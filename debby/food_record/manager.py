import datetime
import io
from abc import ABCMeta, abstractmethod
from io import BytesIO
from typing import List

from PIL import Image
from django.core.files import File
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction
from linebot.models import TextSendMessage

from debby import settings
from food_record.models import FoodModel
from line.callback import FoodRecordCallback
from user.cache import AppCache, FoodData
from user.models import CustomUserModel


class FoodRecordManager(object):
    def __init__(self, callback: FoodRecordCallback):
        self.callback = callback
        self.image_reader = ImageReader()

    def record_image(self, image_content: bytes, extra_info: str):
        current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)

        food_record = FoodModel(user=current_user)
        if extra_info:
            food_record.note = extra_info
        if image_content:
            bytes_io = BytesIO(image_content)
            file = '{0}_food_image.jpg'.format(current_user.line_id)

            food_record.food_image_upload.save(file, File(bytes_io))
        food_record.save()
        return food_record.pk

    @staticmethod
    def reply_to_record_detail_template():
        return TextSendMessage(text='您是否要繼續增加文字說明? (請輸入; 若已完成紀錄請回傳英文字母N )')

    @staticmethod
    def record_extra_info(record_pk: str, text: str):
        food_record = FoodModel.objects.get(pk=record_pk)

        if food_record.note:
            food_record.note += "\n" + text
        else:
            food_record.note = text
        food_record.save()

    @staticmethod
    def handle_final_check_before_save(data: FoodData) -> List[SendMessage]:

        time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S\n")
        message = '{}{}'.format(time, data.extra_info)

        text_send_message = TextSendMessage(text=message)

        send_message = TemplateSendMessage(
            alt_text="您是否確定要存取此次紀錄",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="您是否確定要存取此次紀錄?",
                actions=[
                    PostbackTemplateAction(
                        label='儲存',
                        data='app=FoodRecord&action=CREATE'
                    ),
                    PostbackTemplateAction(
                        label='修改',
                        data='app=FoodRecord&action=MODIFY_EXTRA_INFO'
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data='app=FoodRecord&action=CANCEL'
                    ),
                ]
            )
        )

        return [text_send_message, send_message]

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app="FoodRecord")

        if self.callback.action == 'CREATE_FROM_MENU':
            print("CREATE_FROM_MENU")
            reply = TextSendMessage(text='請上傳一張此次用餐食物的照片,或輸入文字:')

            app_cache.set_next_action(action="WAIT_FOR_USER_REPLY")
            data = FoodData()
            app_cache.data = data
            app_cache.commit()

        elif self.callback.action == "WAIT_FOR_USER_REPLY":
            print("WAIT_FOR_USER_REPLY")
            data = FoodData()
            data.setup_data(app_cache.data)
            if self.callback.text.upper() == 'N':
                reply = self.handle_final_check_before_save(data)
            else:
                if data.extra_info or data.image_id:
                    data.extra_info = "\n".join([data.extra_info, self.callback.text])
                    reply = TextSendMessage(text="繼續說")

                else:
                    data.extra_info = self.callback.text
                    reply = self.reply_to_record_detail_template()
                app_cache.data = data
                app_cache.set_next_action(action="WAIT_FOR_USER_REPLY")
                app_cache.commit()

        elif self.callback.action == "DIRECT_UPLOAD_IMAGE":
            print("DIRECT_UPLOAD_IMAGE")
            data = FoodData()
            data.image_id = self.callback.image_id

            app_cache.data = data
            app_cache.commit()

            reply = self.reply_to_record_detail_template()
            app_cache.set_next_action(action="WAIT_FOR_USER_REPLY")
            app_cache.commit()

        elif self.callback.action == 'CREATE':
            print("CREATE")
            data = FoodData()
            data.setup_data(app_cache.data)

            image_content = self.image_reader.load_image(data.image_id) if data.image_id else None
            food_record_pk = self.record_image(image_content, data.extra_info)

            if food_record_pk:
                app_cache.delete()
                reply = TextSendMessage(text="記錄成功!")
            else:
                reply = TextSendMessage(text="記錄失敗!?")

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

                        message = TextSendMessage(text="繼續說")
                    else:
                        message = TextSendMessage(text="飲食記錄成功!")
                        app_cache.delete()
                    reply = message
        elif self.callback.action == 'MODIFY_EXTRA_INFO':
            reply = TextSendMessage(text="Debby 還不會修改 一起跟Debby努力加油吧!❤")
        elif self.callback.action == 'CANCEL':
            app_cache.delete()
            reply = TextSendMessage(text="記錄取消!")
        return reply


class __AbstractImageReader(metaclass=ABCMeta):
    @abstractmethod
    def load_image(self, image_id) -> bytes:
        pass


class ImageReader(__AbstractImageReader):
    def load_image(self, image_id) -> bytes:
        message_content = settings.LINE_BOT_API.get_message_content(message_id=image_id)
        image = message_content.content
        return image


class MockImageReader(__AbstractImageReader):
    def load_image(self, image_id) -> bytes:
        image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
        byte_arr = io.BytesIO()
        image.save(byte_arr, 'jpeg')
        return byte_arr.getvalue()
