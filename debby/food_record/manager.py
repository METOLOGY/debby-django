from io import BytesIO

from django.core.cache import cache
from django.core.files import File
from linebot.models import ConfirmTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from debby.settings import line_bot_api
from food_record.models import FoodModel
from line.callback import FoodRecordCallback
from user.models import CustomUserModel


class FoodRecordManager:
    def __init__(self, callback: FoodRecordCallback, image_content: bytes):
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
            alt_text='Do you want to record food?',
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
            message = '請輸入補充說明'
        elif self.callback.choice == 'false':
            message = '好的'

        return TextSendMessage(text=message)

    @staticmethod
    def reply_success():
        return TextSendMessage(text="紀錄成功!")

    @staticmethod
    def record_extra_info(record_pk: str, text: str):
        food_record = FoodModel.objects.get(pk=record_pk)
        food_record.note = text
        food_record.save()

    def store_to_user_cache(self, food_record_pk):
        user_cache = cache.get(self.callback.line_id)
        if user_cache:
            user_cache['food_record_pk'] = food_record_pk
            cache.set(self.callback.line_id, user_cache, 120)  # cache for 2 min

    def handle(self) -> SendMessage:
        if self.callback.action == 'reply_if_want_to_record':
            return self.reply_if_user_want_to_record()
        elif self.callback.action == 'CREATE':
            if self.callback.choice == 'true':
                user_cache = cache.get(self.callback.line_id)
                if user_cache:
                    current_user = CustomUserModel.objects.get(line_id=self.callback.line_id)
                    food_record_pk = self.record_image(current_user, self.image_content)
                    self.store_to_user_cache(food_record_pk)

                    return self.reply_record_success_and_if_want_more_detail()

            elif self.callback.choice == 'false':
                return TextSendMessage(text='什麼啊原來只是讓我看看啊')
        elif self.callback.action == 'UPDATE':
            if self.callback.choice == 'true':
                user_cache = cache.get(self.callback.line_id)
                if user_cache and 'food_record_pk' in user_cache.keys():
                    self.record_extra_info(user_cache['food_record_pk'], self.callback.text)
                    return self.reply_success()
        elif self.callback.action == 'write_detail_notes':
            return self.reply_to_record_detail_template()
