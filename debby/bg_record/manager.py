from linebot.models import ConfirmTemplate, ButtonsTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from line.callback import BGRecordCallback
from .models import BGModel
from user.models import CustomUserModel
from user.cache import AppCache


class BGRecordManager:
    line_id = ''
    this_record = BGModel()

    # reminder_message = TemplateSendMessage(
    #     alt_text='嗨，現在要記錄血糖嗎？',
    #     template=ConfirmTemplate(
    #         text='嗨，現在要記錄血糖嗎？',
    #         actions=[
    #             PostbackTemplateAction(
    #                 label='好啊',
    #                 data=BGRecordCallback(line_id=line_id,
    #                                       action='ASK_TO_CREATE',
    #                                       choice='true').url
    #             ),
    #             PostbackTemplateAction(
    #                 label='等等再說',
    #                 data=BGRecordCallback(line_id=line_id,
    #                                       action='ASK_TO_CREATE',
    #                                       choice='false').url
    #             )
    #         ]
    #     )
    # )

    meal_type_message = TemplateSendMessage(
        alt_text='餐前血糖還是飯後血糖呢？',
        template=ButtonsTemplate(
            text='餐前血糖還是飯後血糖呢？',
            actions=[
                PostbackTemplateAction(
                    label='餐前',
                    data=BGRecordCallback(line_id=line_id,
                                          action='SET_TYPE',
                                          choice='before').url
                ),
                PostbackTemplateAction(
                    label='飯後',
                    data=BGRecordCallback(line_id=line_id,
                                          action='SET_TYPE',
                                          choice='after').url
                ),
                PostbackTemplateAction(
                    label='取消紀錄',
                    data=BGRecordCallback(line_id=line_id,
                                          action='SET_TYPE',
                                          choice='cancel').url
                ),
            ]
        )
    )

    confirm_record_message = TextSendMessage(
        alt_text='請問現在要記錄血糖嗎？',
        template=ButtonsTemplate(
            text='請問現在要記錄血糖嗎？',
            actions=[
                PostbackTemplateAction(
                    label='好啊',
                    data=BGRecordCallback(line_id=line_id,
                                          action='CREATE',
                                          choice='true').url
                ),
                PostbackTemplateAction(
                    label='等等再說',
                    data=BGRecordCallback(line_id=line_id,
                                          action='CREATE',
                                          choice='false').url
                )
            ]
        )
    )




    ranges = [70, 80, 130, 250, 600]
    conditions = ["您的血糖過低,請盡速進食! 有低血糖不適症請盡速就醫!",
                  "請注意是否有低血糖不適症情況發生",
                  "Good!血糖控制的還不錯喔!",
                  "血糖還是稍微偏高,要多注意喔!",
                  "注意是否有尿酮酸中毒,若有不適請盡速就醫!",
                  "有高血糖滲透壓症狀疑慮,請盡速就醫!"]

    def __init__(self, callback: BGRecordCallback):
        self.callback = callback

    def reply_by_check_value(self, text: str) -> TextSendMessage:
        value = float(text)
        ind = 0
        for ind, r in enumerate(self.ranges):
            if value <= r:
                break
            elif ind == len(self.ranges) - 1:
                ind += 1
        message = self.conditions[ind]
        return TextSendMessage(text=message)

    # def reply_reminder(self) -> TemplateSendMessage:
    #     return self.reminder_message

    def reply_record_type(self) -> TextSendMessage:
        return self.meal_type_message

    @staticmethod
    def reply_record_success() -> TextSendMessage:
        return TextSendMessage(text='記錄成功！')

    def reply_to_user_choice(self) -> TextSendMessage:
        choice = self.callback.choice
        if choice == 'true':
            return TextSendMessage(text='請輸入血糖數字:')
        elif choice == 'false':
            return TextSendMessage(text='好，要隨時注意自己的血糖狀況哦！')

    @staticmethod
    def reply_please_enter_bg() -> TextSendMessage:
        return TextSendMessage(text='請輸入血糖數字:')

    # @staticmethod
    # def record_bg_record(current_user: CustomUserModel, bg_value: int):
    #     bg = BGModel(user=current_user, glucose_val=bg_value)
    #     bg.save()

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app='BGRecord')

        print('action: ' + self.callback.action)


        self.this_record.user = CustomUserModel.objects.get(line_id=self.callback.line_id)

        if self.callback.action == 'CREATE_FROM_MENU':
            app_cache.set_action('CREATE_FROM_MENU')
            app_cache.commit()
            reply = self.reply_please_enter_bg()

        elif self.callback.action == 'CREATE':
            app_cache.set_action('CREATE')
            app_cache.commit()
            reply = self.reply_record_type()
            self.this_record.glucose_val = int(self.callback.text)

        # elif self.callback.action == 'ASK_TO_CREATE':
        #     app_cache.set_action('ASK_TO_CREATE')
        #     app_cache.commit()
        #     reply = self.reply_to_user_choice()


        elif self.callback.action == 'CONFIRM_RECORD':
            app_cache.set_action('CONFIRM_RECORD')
            app_cache.commit()
            reply = self.reply_to_user_choice()

        elif self.callback.action == 'SET_TYPE':
            app_cache.set_action('CONFIRM_RECORD')
            app_cache.commit()
            print(self.this_record.glucose_val)
            if self.callback.choice == 'cancel':
                # del(self.this_record)
                reply = TextSendMessage(text="okay, 這次就不幫你記錄囉！")
            else:
                self.this_record.type = self.callback.choice
                self.this_record.save()
                reply = TextSendMessage(text=self.reply_record_success().text
                                             + '\n'
                                             + self.reply_by_check_value(self.this_record.glucose_val).text)

        # elif self.callback.action == 'CONFIRM_RECORD':
        #     app_cache.set_action('CONFIRM_RECORD')
        #     app_cache.commit()
        #     reply = self.reply_does_user_want_to_record()

        return reply
