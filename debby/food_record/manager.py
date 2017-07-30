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
import requests
import base64

from debby import settings
from food_record.models import FoodModel, TempImageModel, FoodRecognitionModel
from line.callback import FoodRecordCallback, MyDiaryCallback
from line.constant import FoodRecordAction as Action, MyDiaryAction, RecordType
from user.cache import AppCache, FoodData
from user.models import CustomUserModel


class FoodRecordManager(object):
    def __init__(self, callback: FoodRecordCallback):
        self.callback = callback
        self.image_reader = ImageReader()

    def record_food(self, temp: TempImageModel, food_data:FoodData):
        current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)

        food_record = FoodModel.objects.create(user=current_user,
                                               note=temp.note,
                                               food_image_upload=temp.food_image_upload)
        if food_data.food_name:
            food_record.food_name = food_data.food_name
        if food_data.food_recognition_pk:
            food_record.food_recognition = FoodRecognitionModel.objects.get(id=food_data.food_recognition_pk)

        food_record.time = temp.time
        food_record.save()
        if food_record.food_image_upload.name:
            food_record.make_carousel()

    def reply_to_record_detail_template(self):
        return TemplateSendMessage(
            alt_text="您要繼續增加文字嗎?",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="您要繼續增加文字嗎?",
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

    def reply_if_want_to_record_image(self):
        message = "請問您是想要記錄飲食嗎?"
        return TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label="是，我要記錄此食物照片",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.WAIT_FOR_USER_REPLY).url
                    ),
                    PostbackTemplateAction(
                        label="否，我只是想聊個天",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL_PHOTO).url
                    )
                ]
            )
        )

    def try_delete_temp(self):
        query = TempImageModel.objects.filter(user__line_id=self.callback.line_id)
        if query:
            for temp in query:
                if self.is_temp_expired(temp):
                    temp.delete()


    def select_food_template(self, other_food:list):
        message = '請問是下面其中某一項食物嗎?'
        postbacks = []
        for food in other_food:
            food_name = food['description']
            postbacks.append(
                PostbackTemplateAction(
                    label="{}".format(food_name),
                    data=FoodRecordCallback(self.callback.line_id, action=Action.WAIT_FOR_USER_REPLY, food_name=food_name).url,
                ),
            )
        postbacks.append(
            PostbackTemplateAction(
                label="都不是嗎？",
                data=FoodRecordCallback(self.callback.line_id, action=Action.WAIT_FOR_USER_REPLY,
                                        food_name='').url,
            )
        )

        return TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=postbacks,
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

    @staticmethod
    def delete_temp(temp_id):
        query = TempImageModel.objects.filter(id=temp_id)
        if query:
            temp = query[0]
            temp.delete()

    @staticmethod
    def is_temp_expired(temp: TempImageModel) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = now - temp.create_time
        return True if diff.seconds > 300 else False

    def handle_final_check_before_save(self, data: FoodData) -> TemplateSendMessage:

        text = data.extra_info if data.extra_info else ""

        # Get from temp image
        query = TempImageModel.objects.filter(id=data.record_id)

        photo = None

        if not query:  # create in first time
            user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            temp = TempImageModel.objects.create(user=user,
                                                 note=text)
            image_content = self.image_reader.load_image(data.image_id) if data.image_id else None
            if image_content:
                bytes_io = BytesIO(image_content)
                file = '{0}_food_image.jpg'.format(self.callback.line_id)
                temp.food_image_upload.save(file, File(bytes_io))
                temp.make_carousel()

                host = cache.get("host_name")
                url = temp.carousel.url
                photo = "https://{}{}".format(host, url)
            time = temp.time.strftime("%Y/%m/%d %H:%M:%S\n")
        else:  # may be old or back from my_diary
            temp = query[0]
            text = temp.note
            if temp.food_image_upload:
                host = cache.get("host_name")
                url = temp.carousel.url
                photo = "https://{}{}".format(host, url)
            time = temp.time.strftime("%Y/%m/%d %H:%M:%S\n")

        message = '{}\n{}{}'.format(data.food_name, time, text)

        if len(message) > 60:
            message = message[:50] + "..."

        reply = TemplateSendMessage(
            alt_text="您是否確定要存取此次紀錄?",
            template=ButtonsTemplate(
                title="您是否確定要存取此次紀錄?",
                text=message,
                thumbnail_image_url=photo,
                actions=[
                    PostbackTemplateAction(
                        label='儲存',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CREATE, record_id=temp.id).url
                    ),
                    PostbackTemplateAction(
                        label='修改',
                        data=MyDiaryCallback(self.callback.line_id, action=MyDiaryAction.FOOD_UPDATE,
                                             record_type=RecordType.TEMP_FOOD,
                                             record_id=temp.id).url
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL, record_id=temp.id).url
                    ),
                ]
            )
        )
        return reply

    def handle(self) -> Union[SendMessage, None]:
        reply = TextSendMessage(text='FOOD_RECORD ERROR!')
        app_cache = AppCache(self.callback.line_id)
        app_cache.set_expired_time(seconds=60 * 5)  # set expired time to 5 minutes.
        # always use one object data for each user to save temp image
        self.try_delete_temp()

        if self.callback.action == Action.CREATE_FROM_MENU:
            print(Action.CREATE_FROM_MENU)
            reply = TextSendMessage(text='請上傳一張此次用餐食物的照片,或輸入文字:')

            # init cache again to clean other app's status and data
            app_cache.set_next_action(self.callback.app, action=Action.WAIT_FOR_USER_REPLY)
            data = FoodData()
            app_cache.data = data
            app_cache.commit()

        elif self.callback.action == Action.WAIT_FOR_USER_REPLY:
            print(Action.WAIT_FOR_USER_REPLY)
            data = FoodData()
            data.setup_data(app_cache.data)

            if data.extra_info:
                data.extra_info = "\n".join([data.extra_info, self.callback.text])
            else:
                data.extra_info = self.callback.text

            if self.callback.food_name:
                data.food_name = self.callback.food_name

            reply = self.reply_to_record_detail_template()
            app_cache.data = data
            app_cache.set_next_action(self.callback.app, action=Action.WAIT_FOR_USER_REPLY)
            app_cache.commit()

        elif self.callback.action == Action.DIRECT_UPLOAD_IMAGE:
            print(Action.DIRECT_UPLOAD_IMAGE)
            data = FoodData()
            data.image_id = self.callback.image_id

            # google vision api start here.
            image_content = self.image_reader.load_image(data.image_id) if data.image_id else None
            image_content_base64 = base64.b64encode(image_content)

            req = {
                'requests': [
                    {
                        'image': {
                            'content': image_content_base64.decode('utf-8')
                        },
                        'features': [
                            {
                                "type": "WEB_DETECTION"
                            }
                        ]
                    }
                ]
            }

            r = requests.post('https://vision.googleapis.com/v1/images:annotate?key={}'.format(settings.GOOGLE_VISION_KEY), json=req)
            vision_data = r.json()['responses'][0]['webDetection']

            food_recognition = FoodRecognitionModel()
            if 'webEntities' in vision_data:
                food_recognition.web_entities = vision_data['webEntities']
            if 'pagesWithMatchingImages' in vision_data:
                food_recognition.pages_with_matching_images = vision_data['pagesWithMatchingImages']
            if 'fullMatchingImages' in vision_data:
                food_recognition.full_matching_images = vision_data['fullMatchingImages']
            if 'partialMatchingImages' in vision_data:
                food_recognition.partial_matching_images = vision_data['partialMatchingImages']

            food_recognition.save()

            entities_sorted_by_score = sorted(vision_data['webEntities'], key=lambda x:x['score'], reverse=True)

            data.food_recognition_pk = food_recognition.id
            app_cache.data = data
            app_cache.commit()

            if len(entities_sorted_by_score) <= 3:
                reply = self.select_food_template(entities_sorted_by_score)
            else:
                reply = self.select_food_template(entities_sorted_by_score[0:3])

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

                query = TempImageModel.objects.filter(id=self.callback.record_id)
                if query:
                    temp = query[0]
                    self.record_food(temp, app_cache.data)
                    app_cache.delete()
                    reply = TextSendMessage(text="飲食記錄成功!")
                else:
                    reply = TextSendMessage(text="可能隔太久沒有動作囉, 再重新記錄一次看看?")

                # delete temp image
                self.try_delete_temp()

        elif self.callback.action == Action.CANCEL:
            if not app_cache.data:
                return None
            reply = TextSendMessage(text="記錄取消！您可再從主選單，或直接在對話框上傳一張食物照片就可以記錄飲食囉！")
            self.delete_temp(app_cache.data.record_id) if self.callback.temp_record_id else None
            app_cache.delete()
        elif self.callback.action == Action.CANCEL_PHOTO:
            reply = TextSendMessage(text="哎呀抱歉~Debby不太懂您的意思~還是您想要從主選單開始呢？")
            self.delete_temp(app_cache.data.record_id) if self.callback.temp_record_id else None
            app_cache.delete()
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
