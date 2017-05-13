import datetime
import io
from abc import ABCMeta, abstractmethod
from io import BytesIO
from typing import List, Union

from PIL import Image
from django.core.cache import cache
from django.core.files import File
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, ImageSendMessage
from linebot.models import TextSendMessage

from debby import settings
from food_record.models import FoodModel, TempImageModel
from line.callback import FoodRecordCallback, MyDiaryCallback
from line.constant import FoodRecordAction as Action, App, MyDiaryAction
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

    def reply_to_record_detail_template(self):
        return TemplateSendMessage(
            alt_text="請繼續增加文字說明?",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="請繼續增加文字說明?",
                actions=[
                    PostbackTemplateAction(
                        label="不, 我已輸入完畢!",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CHECK_BEFORE_CREATE).url
                    ),
                    PostbackTemplateAction(
                        label="取消紀錄",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL).url
                    )
                ]
            )
        )

    @staticmethod
    def record_extra_info(record_pk: str, text: str):
        food_record = FoodModel.objects.get(pk=record_pk)

        if food_record.note:
            food_record.note += "\n" + text
        else:
            food_record.note = text
        food_record.save()

    def handle_final_check_before_save(self, data: FoodData) -> List[SendMessage]:
        reply = []
        time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S\n")
        message = '{}{}'.format(time, data.extra_info)

        # Get from temp image
        query = TempImageModel.objects.filter(user__line_id=self.callback.line_id)
        if query:
            temp = query[0]
            host = cache.get("host_name")
            url = temp.image_upload.url
            photo = "https://{}{}".format(host, url)

            image_message = ImageSendMessage(
                original_content_url=photo,
                preview_image_url=photo
            )
            reply.append(image_message)

        text_send_message = TextSendMessage(text=message)

        send_message = TemplateSendMessage(
            alt_text="您是否確定要存取此次紀錄",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="您是否確定要存取此次紀錄?",
                actions=[
                    PostbackTemplateAction(
                        label='儲存',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CREATE).url
                    ),
                    PostbackTemplateAction(
                        label='修改',
                        data=MyDiaryCallback(self.callback.line_id, action=Action.MODIFY_EXTRA_INFO).url
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL).url
                    ),
                ]
            )
        )
        reply.extend((text_send_message, send_message))
        return reply

    def handle(self) -> Union[SendMessage, None]:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app=App.FOOD_RECORD)

        if self.callback.action == Action.CREATE_FROM_MENU:
            print(Action.CREATE_FROM_MENU)
            reply = TextSendMessage(text='請上傳一張此次用餐食物的照片,或輸入文字:')

            app_cache.set_next_action(action=Action.WAIT_FOR_USER_REPLY)
            data = FoodData()
            app_cache.data = data
            app_cache.commit()

        elif self.callback.action == Action.WAIT_FOR_USER_REPLY:
            print(Action.WAIT_FOR_USER_REPLY)
            data = FoodData()
            data.setup_data(app_cache.data)

            if data.extra_info or data.image_id:
                data.extra_info = "\n".join([data.extra_info, self.callback.text])
            else:
                data.extra_info = self.callback.text

            reply = self.reply_to_record_detail_template()
            app_cache.data = data
            app_cache.set_next_action(action=Action.WAIT_FOR_USER_REPLY)
            app_cache.commit()

        elif self.callback.action == Action.DIRECT_UPLOAD_IMAGE:
            print(Action.DIRECT_UPLOAD_IMAGE)
            data = FoodData()
            data.image_id = self.callback.image_id

            # save image to temp folder
            user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            temp, _ = TempImageModel.objects.get_or_create(user=user)
            image_content = self.image_reader.load_image(data.image_id)
            bytes_io = BytesIO(image_content)
            file = '{0}_food_image.jpg'.format(self.callback.line_id)
            temp.image_upload.save(file, File(bytes_io))
            temp.save()

            app_cache.data = data
            app_cache.commit()

            reply = self.reply_to_record_detail_template()
            app_cache.set_next_action(action=Action.WAIT_FOR_USER_REPLY)
            app_cache.commit()

        elif self.callback.action == Action.CHECK_BEFORE_CREATE:
            # avoid cache induced empty error
            if not app_cache.data:
                return None
            print(Action.CHECK_BEFORE_CREATE)
            data = FoodData()
            data.setup_data(app_cache.data) if app_cache.data else None
            reply = self.handle_final_check_before_save(data)

        elif self.callback.action == Action.CREATE:
            # avoid cache induced empty error
            if not app_cache.data:
                reply = TextSendMessage(text="可能隔太久沒有動作囉, 再重新記錄一次看看?")
            else:
                print(Action.CREATE)
                data = FoodData()
                data.setup_data(app_cache.data) if app_cache.data else None

                image_content = self.image_reader.load_image(data.image_id) if data.image_id else None
                food_record_pk = self.record_image(image_content, data.extra_info)

                # delete temp image
                TempImageModel.objects.filter(user__line_id=self.callback.line_id).delete()

                if food_record_pk:
                    app_cache.delete()
                    reply = TextSendMessage(text="飲食記錄成功!")
                else:
                    reply = TextSendMessage(text="記錄失敗!? 可能隔太久沒有動作囉")
        elif self.callback.action == Action.CANCEL:
            if not app_cache.data:
                return None
            app_cache.delete()
            reply = TextSendMessage(text="記錄取消！您可再從主選單，或直接在對話框上傳一張食物照片就可以記錄飲食囉！")
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
