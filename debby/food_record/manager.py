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

    def reply_if_user_want_to_record(self):
        line_id = self.callback.line_id
        return TemplateSendMessage(
            alt_text='請問是否要記錄飲食',
            template=ConfirmTemplate(
                text='請問是否要記錄飲食',
                actions=[
                    PostbackTemplateAction(
                        label='好喔',
                        data=FoodRecordCallback(line_id=line_id, action='CREATE', choice='true').url
                    ),
                    PostbackTemplateAction(
                        label='跟你玩玩的',
                        data=FoodRecordCallback(line_id=line_id, action='CREATE', choice='false').url
                    )
                ]
            )
        )

    def reply_record_success_and_if_want_more_detail(self):
        line_id = self.callback.line_id
        return TemplateSendMessage(
            alt_text='ask if you want to write some note',
            template=ConfirmTemplate(
                text='紀錄成功! 請問是否要補充文字說明? 例如: 1.5份醣類',
                actions=[
                    PostbackTemplateAction(
                        label='好啊',
                        data=FoodRecordCallback(line_id=line_id, action='write_detail_notes', choice='true').url
                    ),
                    PostbackTemplateAction(
                        label='不用了',
                        data=FoodRecordCallback(line_id=line_id, action='write_detail_notes', choice='false').url
                    )
                ]
            )
        )

    def reply_to_record_detail_template(self):
        message = ''

        if self.callback.choice == 'true':
            message = '您是否要繼續增加文字說明? (請輸入; 若已完成紀錄請回傳英文字母N )'
        elif self.callback.choice == 'false':
            message = '好的'

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

    def let_cache_record(self, key: str, value, time: int=60):
        """
        Keep status in cache, identify user by line_id
        :param key: key in cache, must in str
        :param value: value in cache
        :param time: hold the cache in x seconds.
        :return: None
        """
        user_cache = cache.get(self.callback.line_id)
        if user_cache:
            user_cache[key] = value
            cache.set(self.callback.line_id, user_cache, time)

    def handle(self) -> SendMessage:
        if self.callback.action == 'CONFIRM_RECORD':
            return self.reply_if_user_want_to_record()
        elif self.callback.action == 'CREATE':
            if self.callback.choice == 'true':
                user_cache = cache.get(self.callback.line_id)
                print(user_cache)
                if user_cache:
                    current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)
                    food_record_pk = self.record_image(current_user, self.image_content)
                    self.let_cache_record(key='food_record_pk', value=food_record_pk, time=120)
                    print('in\n')
                    return self.reply_record_success_and_if_want_more_detail()
                else:
                    print('passed\n')
                    pass

            elif self.callback.choice == 'false':
                return TextSendMessage(text='什麼啊原來只是讓我看看啊')
        elif self.callback.action == 'UPDATE':
            if self.callback.choice == 'true':
                user_cache = cache.get(self.callback.line_id)
                if user_cache:
                    if 'food_record_pk' in user_cache.keys():
                        if self.callback.text != 'N':
                            self.record_extra_info(user_cache['food_record_pk'], self.callback.text)
                            self.let_cache_record(key='KEEP_RECORDING', value=True, time=60)
                            message = self.reply_keep_recording()
                        else:
                            message = self.reply_record_success()
                            self.delete_cache()
                        return message

        elif self.callback.action == 'write_detail_notes':
            return self.reply_to_record_detail_template()
