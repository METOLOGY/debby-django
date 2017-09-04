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
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, ImageSendMessage
from linebot.models import TextSendMessage

from consult_food.models import WikiFoodTranslateModel, SynonymModel
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
            Action.START: self.wait_for_user_reply,
            Action.WAIT_FOR_USER_REPLY: self.wait_for_user_reply,
            Action.DIRECT_UPLOAD_IMAGE: self.direct_upload_image,
            Action.CHECK_BEFORE_CREATE: self.check_before_create,
            Action.CREATE: self.create,
            Action.CANCEL: self.cancel,
            Action.CANCEL_PHOTO: self.cancel_photo,
            Action.ASK_IF_WANT_TO_RECORD: self.ask_if_want_to_record,
            Action.ASK_IF_WANT_TO_RECORD_WITH_UNKNOWN_NAME: self.ask_if_want_to_record_with_unknown_name,
            Action.CANCEL_RECORD: self.cancel_record,
            Action.REPLY_THANKS: self.reply_thanks,
        }
        self.app_cache = AppCache(self.callback.line_id)

    """
    Reply functions
    """

    def reply_to_record_detail_template(self):
        return TemplateSendMessage(
            alt_text="您要繼續增加文字嗎~直接輸入文字就可以增加文字紀錄!😀",
            template=ButtonsTemplate(
                title="記錄飲食",
                text="您要繼續增加文字嗎~直接輸入文字就可以增加文字紀錄!😀",
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
        message = "請問您是想要記錄飲食嗎～\n😉😉"
        return TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label="我想記錄這個食物",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.START).url
                    ),
                    PostbackTemplateAction(
                        label="我只是想跟你聊聊天~",
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL_PHOTO).url
                    )
                ]
            )
        )

    def reply_modify_or_save_record(self, url: str, food_name: str, time: str, note: str, record_id: int):
        message = '{}\n{}{}'.format(food_name, time, note) if food_name else '{}{}'.format(time, note)
        if len(message) > 60:
            message = message[:50] + "..."

        return TemplateSendMessage(
            alt_text="您是否確定要存取此次紀錄?",
            template=ButtonsTemplate(
                title="您是否確定要存取此次紀錄?",
                text=message,
                thumbnail_image_url=url,
                actions=[
                    PostbackTemplateAction(
                        label='儲存',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CREATE).url
                    ),
                    PostbackTemplateAction(
                        label='修改',
                        data=MyDiaryCallback(self.callback.line_id, action=MyDiaryAction.FOOD_UPDATE,
                                             record_type=RecordType.TEMP_FOOD,
                                             record_id=record_id).url
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data=FoodRecordCallback(self.callback.line_id, action=Action.CANCEL).url
                    ),
                ]
            )
        )

    def reply_is_this_your_meal(self, english_name: str):
        # TODO: implement translate to chinese
        # name = self.translate_to_chinese(english_name)
        name = english_name

        message = "Debby 猜他是 {}".format(name)
        text = TextSendMessage(text=message)

        message = "還是這其實是您的餐點，您想要記錄這次的飲食內容?"

        is_record_food = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[PostbackTemplateAction(label="是",
                                                data=FoodRecordCallback(
                                                    self.callback.line_id,
                                                    action=Action.START).url),
                         PostbackTemplateAction(label="否",
                                                data=FoodRecordCallback(
                                                    self.callback.line_id,
                                                    action=Action.REPLY_THANKS
                                                ).url)
                         ]
            )
        )
        return [text, is_record_food]

    @staticmethod
    def reply_images(synonym_model: SynonymModel):
        nutrition = synonym_model.content_object.nutrition
        count_word = utils.get_count_word(synonym_model.content_object)
        return utils.reply_nutrition(count_word, nutrition)

    # TODO: demo mode
    @staticmethod
    def reply_demo_images():
        reply = []
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
        return reply

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

    """
    reply functions end
    """

    """
    helper functions
    """

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

    def close_future_mode(self):
        cache.delete(self.callback.line_id + '_future')
        cache.delete(self.callback.line_id + '_demo')

    """
    helper functions end
    """

    """
    callbacks 
    """

    def ask_vision_api(self):
        print('ASK_VISION_API')

        image_id = self.callback.image_id
        # google vision api start here.
        image_content = self.image_reader.load_image(image_id) if image_id else None
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

        english_names = [e['description'] for e in entities_sorted_by_score]

        food_names = WikiFoodTranslateModel.objects.translate_to_chinese(english_names)

        self.app_cache.data.temp_image_model.food_recognition = food_recognition
        self.app_cache.commit()

        # TODO: demo mode
        if utils.is_demo_mode_on(self.callback.line_id):
            return self.select_food_template(['潛艇堡', '沙拉', '可頌麵包'])

        if not food_names:
            return self.reply_is_this_your_meal(english_names[0])

        if len(food_names) <= 3:
            reply = self.select_food_template(food_names)
        else:
            reply = self.select_food_template(food_names[0:3])
        return reply

    def ask_if_want_to_record(self):
        print(Action.ASK_IF_WANT_TO_RECORD)
        reply = list()

        food_name = self.callback.food_name
        queryset = SynonymModel.objects.filter(synonym=food_name)
        image_messages = []
        if queryset.exists():
            image_messages = self.reply_images(queryset[0])

        # TODO: demo mode
        if utils.is_demo_mode_on(self.callback.line_id):
            image_messages = self.reply_demo_images()

        reply += image_messages

        question = TemplateSendMessage(
            alt_text='您是否要為此餐點做飲食紀錄呢?',
            template=ButtonsTemplate(
                text='您是否要為此餐點做飲食紀錄呢?',
                actions=[
                    PostbackTemplateAction(
                        label='是',
                        data=FoodRecordCallback(self.callback.line_id,
                                                action=Action.START,
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

    def ask_if_want_to_record_with_unknown_name(self):
        print(Action.ASK_IF_WANT_TO_RECORD_WITH_UNKNOWN_NAME)
        text = TextSendMessage(text="好的Debby會努力學習👩‍🍳 或者您也可以試著換個角度再拍一次？\n"
                                    "盡量只拍攝單品項的菜 Debby比較好懂唷!😃")
        message = "附帶一提，您是否要為此餐點做飲食紀錄呢?"
        question = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label='是',
                        data=FoodRecordCallback(self.callback.line_id,
                                                action=Action.START,
                                                food_name=self.callback.food_name).url
                    ),
                    PostbackTemplateAction(
                        label='否',
                        data=FoodRecordCallback(self.callback.line_id,
                                                action=Action.REPLY_THANKS).url
                    )
                ]
            )
        )
        return [text, question]

    def create_from_menu(self):
        print(Action.CREATE_FROM_MENU)
        reply = TextSendMessage(text='好的😚！請傳給我一張此次用餐食物的照片,或輸入文字:')

        # init cache again to clean other app's status and data
        self.app_cache.set_next_action(self.callback.app, action=Action.START)
        data = FoodData()
        self.app_cache.data = data
        self.app_cache.commit()
        return reply

    def wait_for_user_reply(self):
        if self.callback.action == Action.START:
            print(Action.START)
        else:
            print(Action.WAIT_FOR_USER_REPLY)
        data = FoodData()
        data.setup_data(self.app_cache.data)

        temp_image_model = data.temp_image_model
        if not temp_image_model:
            user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            temp_image_model = TempImageModel.objects.try_delete_and_create(user=user)

        if self.callback.text:
            temp_image_model.add_note(text=self.callback.text)
        if self.callback.food_name:
            temp_image_model.food_name = self.callback.food_name

        reply = self.reply_to_record_detail_template()
        data.temp_image_model = temp_image_model
        self.app_cache.data = data
        self.app_cache.set_next_action(self.callback.app, action=Action.WAIT_FOR_USER_REPLY)
        self.app_cache.commit()
        return reply

    def direct_upload_image(self):
        print(Action.DIRECT_UPLOAD_IMAGE)
        future_mode = utils.is_future_mode_on(self.callback.line_id)

        data = FoodData()
        data.image_id = self.callback.image_id

        image = self.image_reader.load_image(self.callback.image_id)
        image = self.image_reader.to_bytes_io(image_content=image)
        file = '{}_food_image.jpg'.format(self.callback.line_id)

        user = CustomUserModel.objects.get(line_id=self.callback.line_id)
        temp_image_model = TempImageModel.objects.try_delete_and_create(user=user)
        temp_image_model.food_image_upload.save(file, File(image))
        data.temp_image_model = temp_image_model

        self.app_cache.data = data
        self.app_cache.commit()

        if future_mode:
            reply = self.ask_vision_api()
        else:
            reply = self.reply_if_want_to_record_image()

        return reply

    def check_before_create(self):
        # avoid cache induced empty error
        if not self.app_cache.data:
            return None
        print(Action.CHECK_BEFORE_CREATE)
        data = FoodData()
        data.setup_data(self.app_cache.data) if self.app_cache.data else None
        if not data:
            return None

        temp_image_model = data.temp_image_model
        if not temp_image_model:
            temp_image_model = TempImageModel.objects.get(user__line_id=self.callback.line_id)
        if temp_image_model.food_image_upload:
            if not temp_image_model.carousel:
                temp_image_model.make_carousel()
            url = utils.get_image_url(temp_image_model.carousel.url)
        else:
            url = utils.get_image_url('/media/FoodRecord/default.jpg')

        note = temp_image_model.note
        food_name = self.callback.food_name
        if temp_image_model.food_name:
            food_name = temp_image_model.food_name
        if not food_name:
            food_name = ""

        time = temp_image_model.time.astimezone().strftime("%Y/%m/%d %H:%M:%S\n")

        temp_image_model.save()
        data.temp_image_model = temp_image_model
        self.app_cache.data = data
        self.app_cache.commit()

        return self.reply_modify_or_save_record(url, food_name, time, note, temp_image_model.id)

    def create(self):
        print(Action.CREATE)
        # avoid cache induced empty error
        if not self.app_cache.data:
            return TextSendMessage(text="可能隔太久沒有動作囉, 再重新記錄一次看看?")

        data = FoodData()
        data.setup_data(self.app_cache.data) if self.app_cache.data else None
        if not data:
            return None

        temp_image_model = data.temp_image_model
        FoodModel.objects.create(user=temp_image_model.user,
                                 note=temp_image_model.note,
                                 food_image_upload=temp_image_model.food_image_upload,
                                 food_recognition=temp_image_model.food_recognition,
                                 food_name=temp_image_model.food_name,
                                 carousel=temp_image_model.carousel,
                                 time=temp_image_model.time)

        self.app_cache.delete()
        self.close_future_mode()
        return TextSendMessage(text="耶～～您的飲食記錄成功！🎉🎉🎉")

    def cancel(self):
        print(Action.CANCEL)
        if not self.app_cache.data:
            return None
        reply = TextSendMessage(text="記錄取消！您可再從主選單，或直接在對話框上傳一張食物照片就可以記錄飲食囉！")
        self.app_cache.delete()
        self.close_future_mode()
        return reply

    def cancel_photo(self):
        print(Action.CANCEL_PHOTO)
        reply = TextSendMessage(text="好呀，你應該不是只想給我看這張照片對吧? 我們來聊聊天吧!")
        self.app_cache.delete()
        return reply

    def cancel_record(self):
        print(Action.CANCEL_RECORD)
        self.close_future_mode()
        return TextSendMessage(text='好的，希望 Debby 有幫助到您^^')

    def reply_thanks(self):
        print(Action.REPLY_THANKS)
        self.close_future_mode()
        return TextSendMessage(text='希望你能喜歡新功能^^')

    def handle(self) -> Union[SendMessage, None]:
        self.app_cache.set_expired_time(seconds=60 * 5)  # set expired time to 5 minutes.
        # always use one object data for each user to save temp image
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

    @staticmethod
    def to_bytes_io(image_content: bytes) -> BytesIO:
        return BytesIO(image_content)


class MockImageReader(__AbstractImageReader):
    def load_image(self, image_id) -> bytes:
        image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
        byte_arr = io.BytesIO()
        image.save(byte_arr, 'jpeg')
        return byte_arr.getvalue()
