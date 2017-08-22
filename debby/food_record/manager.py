import base64
import datetime
import io
import json
from abc import ABCMeta, abstractmethod
from io import BytesIO
from typing import Union, List

import requests
from PIL import Image
from django.core.cache import cache
from django.core.files import File
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, ImageSendMessage, \
    MessageTemplateAction
from linebot.models import TextSendMessage

from consult_food.models import WikiFoodTranslateModel
from debby import settings, utils
from food_record.models import FoodModel, TempImageModel, FoodRecognitionModel
from line.callback import FoodRecordCallback, MyDiaryCallback
from line.constant import FoodRecordAction as Action, MyDiaryAction, RecordType
from user.cache import AppCache, FoodData
from user.models import CustomUserModel


class FoodRecordManager(object):
    def __init__(self, callback: FoodRecordCallback):
        self.callback = callback
        self.image_reader = ImageReader()
        self.registered_actions = {
            Action.CREATE_FROM_MENU: self.create_from_menu,
            Action.WAIT_FOR_USER_REPLY: self.wait_for_user_reply,
            Action.DIRECT_UPLOAD_IMAGE: self.direct_upload_image,
            Action.CHECK_BEFORE_CREATE: self.check_before_create,
            Action.CREATE: self.create,
            Action.CANCEL: self.cancel,
            Action.CANCEL_PHOTO: self.cancel_photo,
            Action.ASK_IF_WANT_TO_RECORD: self.ask_if_want_to_record,
            Action.ASK_IF_WANT_TO_RECORD_WITH_UNKNOWN_NAME: self.ask_if_want_to_record_with_unknown_name,
            Action.CANCEL_RECORD: self.cancel_record
        }
        self.app_cache = AppCache(self.callback.line_id)

    def record_food(self, temp: TempImageModel, food_data: FoodData):
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
            alt_text="您還有想增加甚麼文字嗎～",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="您要繼續增加文字嗎?",
                actions=[
                    PostbackTemplateAction(
                        label="沒有了，我都輸入好了！",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CHECK_BEFORE_CREATE).url
                    ),
                    PostbackTemplateAction(
                        label="我想取消這個記錄...",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL).url
                    )
                ]
            )
        )

    def reply_if_want_to_record_image(self):
        message = "請問您是想要記錄飲食嗎～😉😉"
        return TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label="對喔！我想留下這個食物的記錄",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.WAIT_FOR_USER_REPLY).url
                    ),
                    PostbackTemplateAction(
                        label="沒有啦～我只是想跟你聊聊天",
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

    def select_food_template(self, other_food: List[str]):
        message = '請問是下面其中某一項食物嗎?' if len(other_food) > 0 else '無法辨識食物，建議一次只拍一種食物就好囉!'
        negative_message = '都不是嗎？' if len(other_food) > 0 else '沒關係～'
        postbacks = []
        for food_name in other_food:
            postbacks.append(
                PostbackTemplateAction(
                    label="{}".format(food_name),
                    data=FoodRecordCallback(self.callback.line_id,
                                            action=Action.ASK_IF_WANT_TO_RECORD,
                                            food_name=food_name).url,
                ),
            )
        postbacks.append(
            PostbackTemplateAction(
                label=negative_message,
                data=FoodRecordCallback(self.callback.line_id,
                                        action=Action.ASK_IF_WANT_TO_RECORD_WITH_UNKNOWN_NAME,
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
            time = temp.time.astimezone().strftime("%Y/%m/%d %H:%M:%S\n")
        else:  # may be old or back from my_diary
            temp = query[0]
            text = temp.note
            if temp.food_image_upload:
                host = cache.get("host_name")
                url = temp.carousel.url
                photo = "https://{}{}".format(host, url)
            time = temp.time.astimezone().strftime("%Y/%m/%d %H:%M:%S\n")

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

    def ask_vision_api(self):
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

        r = requests.post('https://vision.googleapis.com/v1/images:annotate?key={}'.format(settings.GOOGLE_VISION_KEY),
                          json=req)
        vision_data = r.json()['responses'][0]['webDetection']

        food_recognition = FoodRecognitionModel()
        if 'webEntities' in vision_data:
            food_recognition.web_entities = json.dumps(vision_data['webEntities'])
        if 'pagesWithMatchingImages' in vision_data:
            food_recognition.pages_with_matching_images = json.dumps(vision_data['pagesWithMatchingImages'])
        if 'fullMatchingImages' in vision_data:
            food_recognition.full_matching_images = json.dumps(vision_data['fullMatchingImages'])
        if 'partialMatchingImages' in vision_data:
            food_recognition.partial_matching_images = json.dumps(vision_data['partialMatchingImages'])

        food_recognition.save()

        entities_sorted_by_score = sorted(vision_data['webEntities'], key=lambda x: x['score'], reverse=True)
        entities_sorted_by_score = [x for x in entities_sorted_by_score if 'description' in x]

        entities_sorted_by_score_zh_tw = []
        for ent in entities_sorted_by_score:
            try:
                obj = WikiFoodTranslateModel.objects.get(english=ent)
                entities_sorted_by_score_zh_tw.append(obj.chinese['description'])
            except WikiFoodTranslateModel.DoesNotExist:
                pass

        data.food_recognition_pk = food_recognition.id
        self.app_cache.data = data
        self.app_cache.commit()

        # TODO: demo mode
        if utils.is_demo_mode_on(self.callback.line_id):
            reply = self.select_food_template(['潛艇堡', '沙拉', '可頌麵包'])
        else:
            if len(entities_sorted_by_score_zh_tw) <= 3:
                reply = self.select_food_template(entities_sorted_by_score_zh_tw)
            else:
                reply = self.select_food_template(entities_sorted_by_score_zh_tw[0:3])
        return reply

    def create_from_menu(self):
        print(Action.CREATE_FROM_MENU)
        reply = TextSendMessage(text='好的😚！請傳給我一張此次用餐食物的照片,或輸入文字:')

        # init cache again to clean other app's status and data
        self.app_cache.set_next_action(self.callback.app, action=Action.WAIT_FOR_USER_REPLY)
        data = FoodData()
        self.app_cache.data = data
        self.app_cache.commit()
        return reply

    def wait_for_user_reply(self):
        print(Action.WAIT_FOR_USER_REPLY)
        data = FoodData()
        data.setup_data(self.app_cache.data)

        if data.extra_info:
            data.extra_info = "\n".join([data.extra_info, self.callback.text])
        else:
            data.extra_info = self.callback.text

        if self.callback.food_name:
            data.food_name = self.callback.food_name

        reply = self.reply_to_record_detail_template()
        self.app_cache.data = data
        self.app_cache.set_next_action(self.callback.app, action=Action.WAIT_FOR_USER_REPLY)
        self.app_cache.commit()
        return reply

    def direct_upload_image(self):
        print(Action.DIRECT_UPLOAD_IMAGE)
        future_mode = utils.is_future_mode_on(self.callback.line_id)

        if future_mode:
            reply = self.ask_vision_api()
        else:
            data = FoodData()
            data.image_id = self.callback.image_id

            self.app_cache.data = data
            self.app_cache.commit()

            reply = self.reply_if_want_to_record_image()

        return reply

    def check_before_create(self):
        # avoid cache induced empty error
        if not self.app_cache.data:
            return None
        print(Action.CHECK_BEFORE_CREATE)
        data = FoodData()
        data.setup_data(self.app_cache.data) if self.app_cache.data else None
        reply = self.handle_final_check_before_save(data)
        return reply

    def create(self):
        # avoid cache induced empty error
        if not self.app_cache.data:
            reply = TextSendMessage(text="可能隔太久沒有動作囉, 再重新記錄一次看看?")
        else:
            print(Action.CREATE)
            data = FoodData()
            data.setup_data(self.app_cache.data) if self.app_cache.data else None

            query = TempImageModel.objects.filter(id=self.callback.record_id)
            if query:
                temp = query[0]
                self.record_food(temp, self.app_cache.data)
                self.app_cache.delete()
                cache.delete(self.callback.line_id + '_future')
                cache.delete(self.callback.line_id + '_demo')
                reply = TextSendMessage(text="耶～～您的飲食記錄成功！🎉🎉🎉")
            else:
                reply = TextSendMessage(text="可能隔太久沒有動作囉, 再重新記錄一次看看?")

            # delete temp image
            self.try_delete_temp()
        return reply

    def cancel(self):
        if not self.app_cache.data:
            return None
        reply = TextSendMessage(text="記錄取消！您可再從主選單，或直接在對話框上傳一張食物照片就可以記錄飲食囉！")
        self.delete_temp(self.app_cache.data.record_id) if self.callback.temp_record_id else None
        self.app_cache.delete()
        return reply

    def cancel_photo(self):
        reply = TextSendMessage(text="哎呀抱歉~Debby不太懂您的意思~還是您想要從主選單開始呢？")
        self.delete_temp(self.app_cache.data.record_id) if self.callback.temp_record_id else None
        self.app_cache.delete()
        return reply

    def ask_if_want_to_record(self):
        print(Action.ASK_IF_WANT_TO_RECORD)
        reply = list()

        # TODO: 之後要補上非 demo 時的流程
        if utils.is_demo_mode_on(self.callback.line_id):
            text_message = TextSendMessage(text="每一份")
            reply.append(text_message)

            url = 'media/ConsultFood/nutrition_amount/demo.jpeg'
            preview_url = 'media/ConsultFood/nutrition_amount_preview/demo.jpeg'

            # host = cache.get("host_name")
            host = 'debby.metology.com.tw/'
            photo = "https://{}/{}".format(host, url)
            preview_photo = "https://{}/{}".format(host, preview_url)
            calories = ImageSendMessage(original_content_url=photo,
                                        preview_image_url=preview_photo)
            reply.append(calories)

            url = 'media/ConsultFood/six_group_portion/demo.jpeg'
            preview_url = 'media/ConsultFood/six_group_portion_preview/demo.jpeg'

            # host = cache.get("host_name")
            host = 'debby.metology.com.tw/'
            photo = "https://{}/{}".format(host, url)
            preview_photo = "https://{}/{}".format(host, preview_url)
            six_group = ImageSendMessage(original_content_url=photo,
                                         preview_image_url=preview_photo)
            reply.append(six_group)

        question = TemplateSendMessage(
            alt_text='您是否要為此餐點做飲食紀錄呢?',
            template=ButtonsTemplate(
                text='您是否要為此餐點做飲食紀錄呢?',
                actions=[
                    PostbackTemplateAction(
                        label='是',
                        data=FoodRecordCallback(self.callback.line_id,
                                                action=Action.WAIT_FOR_USER_REPLY,
                                                food_name=self.callback.food_name).url
                    ),
                    PostbackTemplateAction(
                        label='否',
                        data=FoodRecordCallback(self.callback.line_id,
                                                action=Action.CANCEL_RECORD,
                                                food_name=self.callback.food_name).url
                    )
                ]
            )
        )
        reply.append(question)

        return reply

    # TODO: 補上 好的Debby會盡量學習! 您是否要為此餐點做飲食紀錄呢? 的邏輯
    def ask_if_want_to_record_with_unknown_name(self):
        pass

    def cancel_record(self):
        cache.delete(self.callback.line_id + '_future')
        cache.delete(self.callback.line_id + '_demo')
        return TextSendMessage(text='好的，希望 Debby 有幫助到您^^')

    def handle(self) -> Union[SendMessage, None]:
        self.app_cache.set_expired_time(seconds=60 * 5)  # set expired time to 5 minutes.
        # always use one object data for each user to save temp image
        self.try_delete_temp()

        return self.registered_actions[self.callback.action]()


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
