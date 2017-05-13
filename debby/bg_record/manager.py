from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from chat.manager import ChatManager
from line.callback import BGRecordCallback
from line.callback import ChatCallback
from line.constant import BGRecordAction as Action, App
from reminder.models import UserReminder
from user.cache import AppCache
from user.cache import BGData
from user.models import CustomUserModel
from .models import BGModel


class BGRecordManager:
    this_record = BGModel()

    ranges = [70, 80, 130, 250, 600]
    conditions = ["您的血糖過低,請盡速進食! 有低血糖不適症請盡速就醫!",
                  "請注意是否有低血糖不適症情況發生",
                  "Good!血糖控制的還不錯喔!",
                  "血糖還是稍微偏高,要多注意喔!",
                  "注意是否有尿酮酸中毒,若有不適請盡速就醫!",
                  "有高血糖滲透壓症狀疑慮,請盡速就醫!"]

    def __init__(self, callback: BGRecordCallback):
        self.callback = callback

    def is_input_a_bg_value(self):
        """
        Check the int input from user is a blood glucose value or not.
        We defined the blood value is between 20 to 999
        :return: boolean
        """
        return self.callback.text.isdigit() and 20 < int(self.callback.text) < 999

    @staticmethod
    def reply_bg_range_not_right():
        return TextSendMessage(text='您輸入的血糖範圍好像怪怪的，請確認血糖範圍在20 ~ 999之間～')

    def reply_by_check_value(self, value: int) -> TextSendMessage:
        value = float(value)
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

    def reply_record_type(self) -> TemplateSendMessage:
        return TemplateSendMessage(
            alt_text='餐前血糖還是飯後血糖呢？',
            template=ButtonsTemplate(
                text='餐前血糖還是飯後血糖呢？',
                actions=[
                    PostbackTemplateAction(
                        label='餐前',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.SET_TYPE,
                            choice='before').url
                    ),
                    PostbackTemplateAction(
                        label='飯後',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.SET_TYPE,
                            choice='after').url
                    ),
                    PostbackTemplateAction(
                        label='取消紀錄',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.SET_TYPE,
                            choice='cancel').url
                    ),
                ]
            )
        )

    @staticmethod
    def reply_record_success() -> TextSendMessage:
        return TextSendMessage(text='記錄成功！')

    # def reply_to_user_choice(self) -> TextSendMessage:
    #     choice = self.callback.choice
    #     if choice == 'true':
    #         return TextSendMessage(text='請輸入血糖數字:')
    #     elif choice == 'false':
    #         return TextSendMessage(text='好，要隨時注意自己的血糖狀況哦！')

    @staticmethod
    def reply_please_enter_bg() -> TextSendMessage:
        return TextSendMessage(text='請輸入血糖數字:')

    def reply_confirm_record(self) -> TemplateSendMessage:
        return TemplateSendMessage(
            alt_text='請問現在要記錄血糖嗎？',
            template=ButtonsTemplate(
                text='請問現在要記錄血糖嗎？',
                actions=[
                    PostbackTemplateAction(
                        label='好啊',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.CONFIRM_RECORD,
                            choice='yes').url
                    ),
                    PostbackTemplateAction(
                        label='等等再說',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.CONFIRM_RECORD,
                            choice='no').url
                    )
                ]
            )
        )

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app=App.BG_RECORD)

        self.this_record.user = CustomUserModel.objects.get(line_id=self.callback.line_id)

        if self.callback.action == Action.CREATE_FROM_MENU:
            app_cache.set_next_action(Action.CREATE_FROM_MENU)
            app_cache.commit()
            print(self.callback.text.isdigit())
            if self.callback.text.isdigit() and self.is_input_a_bg_value():
                self.this_record.glucose_val = int(self.callback.text)
                reply = self.reply_record_type()
            elif self.callback.text.isdigit() and self.is_input_a_bg_value() is False:
                reply = [
                    self.reply_bg_range_not_right(),
                    self.reply_please_enter_bg(),
                ]
            else:
                # make sure that app name is right, when the process comes from reminder app.
                app_cache.app = App.BG_RECORD
                app_cache.commit()
                reply = self.reply_please_enter_bg()

        elif self.callback.action == Action.CREATE_FROM_VALUE:
            app_cache.set_next_action(Action.CONFIRM_RECORD)
            data = BGData()
            data.text = self.callback.text
            app_cache.data = data
            app_cache.commit()

            reply = self.reply_confirm_record()

        elif self.callback.action == Action.CONFIRM_RECORD:

            if self.callback.choice == 'yes':
                text = app_cache.data.text
                self.this_record.glucose_val = int(text)

                reply = self.reply_record_type()
            elif self.callback.choice == 'no':

                # to chat manager
                # TODO: 這裡有點笨
                callback = ChatCallback(line_id=self.callback.line_id,
                                        text=app_cache.data.text)

                reply = ChatManager(callback).handle()

        elif self.callback.action == Action.SET_TYPE:
            if self.callback.choice == 'cancel':
                reply = TextSendMessage(text="okay, 這次就不幫你記錄囉！")
            else:
                self.this_record.type = self.callback.choice
                self.this_record.save()

                reply_common = [
                    self.reply_record_success(),
                    self.reply_by_check_value(self.this_record.glucose_val)
                ]

                try:
                    if app_cache.data.reminder_id:
                        id_ = app_cache.data.reminder_id

                        # repeated code here
                        # TODO: figure out solutions for app communication without looping import.
                        reminder = UserReminder.objects.get(id=id_)
                        reminders = UserReminder.objects.filter(user=reminder.user, type=reminder.type)
                        time = []
                        for re in reminders:
                            time.append(re.time)
                        time = sorted(time)
                        index = time.index(reminder.time)
                        next_reminders = UserReminder.objects.filter(user=reminder.user, type=reminder.type,
                                                                     time=time[index + 1])
                        next_reminder = next_reminders[0] if next_reminders else None

                        type_ = reminder.type
                        type_zh = ''
                        if type_ == 'bg':
                            type_zh = '血糖'
                        elif type_ == 'insulin':
                            type_zh = '胰島素'
                        elif type_ == 'drug':
                            type_zh = '藥物'

                        if next_reminder is not None:
                            reply = reply_common + [
                                TextSendMessage(text='下一次量測{}提醒時間是: {}'.format(type_zh, next_reminder.time)),
                                TextSendMessage(text='您可至"我的設定"中調整提醒時間')
                            ]
                        else:
                            reply = reply_common + [
                                TextSendMessage(text='您今日已沒有下一次的提醒項目!'),
                                TextSendMessage(text='您可至"我的設定"中調整提醒時間')
                            ]
                except:
                    # TODO: Not recommend using try/except, it's not clear and explicit where it will throw to here.
                    reply = reply_common

                    # clear cache
            app_cache.delete()

        return reply
