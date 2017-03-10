from io import BytesIO

from django.core.files import File
from linebot.models import ConfirmTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from food_record.models import FoodModel
from user.models import CustomUserModel


class FoodRecordManager:
<<<<<<< Updated upstream
=======
    def __init__(self, line_bot_api: LineBotApi, event: MessageEvent):
        self.line_bot_api = line_bot_api
        self.event = event
>>>>>>> Stashed changes

    @staticmethod
    def record_image(current_user: CustomUserModel, image_content: bytes):
        food_record = FoodModel(user=current_user)
        io = BytesIO(image_content)

        food_record.food_image_upload.save('{0}_food_image.jpg'.format(current_user.line_id), File(io))
        return food_record.pk

    @staticmethod
    def reply_if_user_want_to_record():
        return TemplateSendMessage(
            alt_text='Do you want to record food?',
            template=ConfirmTemplate(
                text='請問是否要記錄飲食',
                actions=[
                    PostbackTemplateAction(
                        label='好喔',
                        data='callback=FoodRecord&action=record&choice=true'
                    ),
                    PostbackTemplateAction(
                        label='跟你玩玩的',
                        data='callback=FoodRecord&action=record&choice=false'
                    )
                ]
            )
        )

    @staticmethod
    def reply_record_success_and_if_want_more_detail():
        return TemplateSendMessage(
            alt_text='ask if you want to write some note',
            template=ConfirmTemplate(
                text='紀錄成功! 請問是否要補充文字說明? 例如: 1.5份醣類',
                actions=[
                    PostbackTemplateAction(
                        label='好啊',
                        data='callback=FoodRecord&action=write_other_notes&choice=true'
                    ),
                    PostbackTemplateAction(
                        label='不用了',
                        data='callback=FoodRecord&action=write_other_notes&choice=false'
                    )
                ]
            )
        )

    @staticmethod
    def reply_to_record_detail_template(data):
        choice = data['choice']
        message = ''

        if choice == 'true':
            message = '請輸入補充說明'
            # line_id = self._get_line_id()
            # user_cache = cache.get(line_id)
            # user_cache['event'] = 'record_food_detail'
            # cache.set(line_id, user_cache, 300)
        elif choice == 'false':
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

<<<<<<< Updated upstream
=======
        message = '紀錄成功!'
        cache.delete(line_id)
        self._reply_text_send_message(message)

    def ask_user_upload_an_image(self):
        self._reply_text_send_message('請上傳一張照片')
>>>>>>> Stashed changes
