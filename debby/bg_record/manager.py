from datetime import datetime
from typing import Optional

from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import SendMessage
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from chat.manager import ChatManager
from line.callback import BGRecordCallback
from line.callback import ChatCallback
from line.constant import BGRecordAction as Action
from reminder.models import UserReminder
from user.cache import AppCache
from user.cache import BGData
from user.models import CustomUserModel
from .models import BGModel, DrugIntakeModel, InsulinIntakeModel


class BGRecordManager:
    before_ranges = [70, 80, 130, 250, 600]
    before_conditions = ["您的血糖過低,請盡速進食! 有低血糖不適症請盡速就醫!",
                         "請注意是否有低血糖不適症情況發生",
                         "Good!血糖控制的還不錯喔!記得繼續保持👍",
                         "血糖還是稍微偏高,要多注意喔!",
                         "注意是否有尿酮酸中毒,若有不適請盡速就醫!",
                         "有高血糖滲透壓症狀疑慮,請盡速就醫!"]
    after_ranges = [70, 120, 160, 250, 600]
    after_conditions = ["您的血糖過低,請盡速進食! 有低血糖不適症請盡速就醫!",
                        "吃飽了嗎?可以考慮再吃一些水果喔!",
                        "Good!飯後血糖落於正常值喔!記得繼續保持👍",
                        "血糖還是稍微偏高,要多注意喔!",
                        "血糖太高了! 請考慮立刻使用藥物控制! ",
                        "有高血糖滲透壓症狀疑慮,請盡速就醫!"]

    def __init__(self, callback: BGRecordCallback):
        self.callback = callback
        self.app_cache = AppCache(self.callback.line_id)
        self.registered_actions = {
            Action.CREATE_FROM_MENU: self.create_from_menu,
            Action.CREATE_FROM_VALUE: self.create_from_value,
            Action.CONFIRM_RECORD: self.confirm_record,
            Action.SET_TYPE: self.set_type,
            Action.CREATE_DRUG_RECORD: self.create_record,
            Action.CREATE_INSULIN_RECORD: self.create_record,
            Action.CREATE_DRUG_RECORD_CANCEL: self.create_cancel,
            Action.CREATE_DRUG_RECORD_CONFIRM: self.create_drug_record_confirm,
            Action.CREATE_INSULIN_RECORD_CONFIRM: self.create_insulin_record_confirm,
        }

    """
    Reply functions
    """

    @staticmethod
    def reply_bg_range_not_right():
        return TextSendMessage(text='您輸入的血糖範圍好像怪怪的，請確認血糖範圍在20 ~ 999之間～')

    def reply_value_condition_by_check_value(self, choice: str, value: int) -> TextSendMessage:
        value = float(value)
        message = None
        if choice == 'before':
            ind = self.get_range_index(self.before_ranges, value)
            message = self.before_conditions[ind]
        elif choice == 'after':
            ind = self.get_range_index(self.after_ranges, value)
            message = self.after_conditions[ind]
        return TextSendMessage(text=message)

    def reply_record_type(self, glucose_val) -> TemplateSendMessage:
        return TemplateSendMessage(
            alt_text='那...是餐前還是飯後血糖呢😄？',
            template=ButtonsTemplate(
                text='那...是餐前還是飯後血糖呢😄？',
                actions=[
                    PostbackTemplateAction(
                        label='餐前',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.SET_TYPE,
                            choice='before',
                            glucose_val=glucose_val
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='飯後',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.SET_TYPE,
                            choice='after',
                            glucose_val=glucose_val
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='我想取消...',
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

    @staticmethod
    def reply_record_invalid():
        return TextSendMessage(text='請輸入數字才能紀錄血糖哦！')

    @staticmethod
    def reply_please_enter_bg() -> TextSendMessage:
        return TextSendMessage(text='好的😚！請告訴我您的血糖數字:')

    def reply_confirm_record(self, input_text) -> TemplateSendMessage:
        return TemplateSendMessage(
            alt_text='請問您是想要記錄血糖嗎～😉😉',
            template=ButtonsTemplate(
                text='請問您是想要記錄血糖嗎～😉😉',
                actions=[
                    PostbackTemplateAction(
                        label='對喔！我想留下這次的血糖數字！',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.CONFIRM_RECORD,
                            choice='yes',
                            text=input_text,
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='沒有啦！我只是想跟你聊聊天～',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=Action.CONFIRM_RECORD,
                            choice='no',
                            text=input_text,
                        ).url
                    )
                ]
            )
        )

    @staticmethod
    def reply_ok_dont_record() -> TextSendMessage:
        message = "Okay, 這次就不幫你記錄囉！"
        return TextSendMessage(text=message)

    def reply_check_user_intent_to_save(self, show_time: str, confirm_action: str, cancel_action: str):
        return TemplateSendMessage(
            alt_text='您是否確定儲存這次紀錄？',
            template=ButtonsTemplate(
                text='您是否確定儲存這次紀錄: {}？'.format(show_time),
                actions=[
                    PostbackTemplateAction(
                        label='確定',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=confirm_action
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=cancel_action
                        ).url
                    )
                ]
            )
        )

    """
    Reply end
    """

    """
    Helper functions
    """

    def is_input_a_bg_value(self):
        """
        Check the int input from user is a blood glucose value or not.
        We defined the blood value is between 20 to 999
        :return: boolean
        """
        return self.callback.text.isdigit() and 20 < int(self.callback.text) < 999

    @staticmethod
    def get_range_index(ranges: list, value: float):
        ind = 0
        for ind, r in enumerate(ranges):
            if value <= r:
                break
            elif ind == len(ranges) - 1:
                ind += 1
        return ind

    def setup_reminder(self):
        id_ = self.app_cache.data.reminder_id

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
            reply = [
                TextSendMessage(text='下一次量測{}提醒時間是: {}'.format(type_zh, next_reminder.time)),
                TextSendMessage(text='您可至"我的設定"中調整提醒時間')
            ]
        else:
            reply = [
                TextSendMessage(text='您今日已沒有下一次的提醒項目!'),
                TextSendMessage(text='您可至"我的設定"中調整提醒時間')
            ]
        return reply

    @staticmethod
    def get_next_action(action: str):
        if action == Action.CREATE_DRUG_RECORD:
            confirm_action = Action.CREATE_DRUG_RECORD_CONFIRM
            cancel_action = Action.CREATE_DRUG_RECORD_CANCEL
        else:
            confirm_action = Action.CREATE_INSULIN_RECORD_CONFIRM
            cancel_action = Action.CREATE_INSULIN_RECORD_CANCEL
        return confirm_action, cancel_action

    """
    Helper functions end
    """

    """
    Registered functions
    """

    def create_from_menu(self):
        print(Action.CREATE_FROM_MENU)
        # init cache again to clean other app's status and data
        self.app_cache.set_next_action(self.callback.app, action=Action.CREATE_FROM_VALUE)
        self.app_cache.commit()
        reply = self.reply_please_enter_bg()
        return reply

    def create_from_value(self):
        print(Action.CREATE_FROM_VALUE)
        if self.callback.text.isdigit() and self.is_input_a_bg_value():
            reply = self.reply_confirm_record(self.callback.text)
        elif self.callback.text.isdigit() and not self.is_input_a_bg_value():
            reply = [
                self.reply_bg_range_not_right(),
                self.reply_please_enter_bg()
            ]
        else:
            reply = [
                self.reply_record_invalid(),
                self.reply_please_enter_bg()
            ]
        return reply

    def confirm_record(self):
        print(Action.CONFIRM_RECORD)
        if self.callback.choice == 'yes':
            glucose_val = int(self.callback.text)
            return self.reply_record_type(glucose_val)
        elif self.callback.choice == 'no':
            self.app_cache.delete()
            callback = ChatCallback(self.callback.line_id,
                                    text=self.callback.text)
            return ChatManager(callback).handle()

    def set_type(self):
        print(Action.SET_TYPE)
        if self.callback.choice == 'cancel':
            reply = self.reply_ok_dont_record()
        else:
            user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            record = BGModel.objects.create(user=user,
                                            type=self.callback.choice,
                                            glucose_val=self.callback.glucose_val)

            reply_common = [
                self.reply_record_success(),
                self.reply_value_condition_by_check_value(self.callback.choice, record.glucose_val)
            ]

            if hasattr(self.app_cache.data, 'reminder_id'):
                reminder_replies = self.setup_reminder()
                reply = reply_common + reminder_replies
            else:
                reply = reply_common

        self.app_cache.delete()

        return reply

    def create_record(self):
        if self.callback.action == Action.CREATE_INSULIN_RECORD:
            print(Action.CREATE_INSULIN_RECORD)
        elif self.callback.action == Action.CREATE_DRUG_RECORD:
            print(Action.CREATE_DRUG_RECORD)

        time = datetime.now()
        show_time = time.astimezone().strftime('%Y/%m/%d %H:%M')
        data = BGData()
        data.record_time = time
        self.app_cache.save_data(data)

        [confirm_action, cancel_action] = self.get_next_action(self.callback.action)

        return self.reply_check_user_intent_to_save(show_time, confirm_action, cancel_action)

    def create_cancel(self):
        message = ''
        if self.callback.action == Action.CREATE_INSULIN_RECORD_CANCEL:
            print(Action.CREATE_INSULIN_RECORD_CANCEL)
            message = '好的！您可再從主選單記錄服用藥物的時間喔！'

        elif self.callback.action == Action.CREATE_DRUG_RECORD_CANCEL:
            print(Action.CREATE_DRUG_RECORD_CANCEL)
            message = '好的！您可再從主選單選擇記錄血糖的時間喔！'

        self.app_cache.delete()
        return TextSendMessage(text=message)

    def create_drug_record_confirm(self):
        print(Action.CREATE_DRUG_RECORD_CONFIRM)
        record_time = self.app_cache.data.record_time
        user = CustomUserModel.objects.get(line_id=self.callback.line_id)
        DrugIntakeModel.objects.create(user=user,
                                       time=record_time,
                                       status=True)

        self.app_cache.delete()
        reply = TextSendMessage(text='紀錄成功！您可在我的日記裡，查看最近的紀錄！')
        return reply

    def create_insulin_record_confirm(self):
        print(Action.CREATE_INSULIN_RECORD_CONFIRM)
        record_time = self.app_cache.data.record_time
        user = CustomUserModel.objects.get(line_id=self.callback.line_id)
        InsulinIntakeModel.objects.create(user=user,
                                          time=record_time,
                                          status=True)

        self.app_cache.delete()
        reply = TextSendMessage(text='耶～～您的血糖記錄成功啦！🎉🎉🎉！您可在我的日記裡，查看最近的紀錄！')
        return reply

    """
    Registered functions end
    """

    def handle(self) -> Optional[SendMessage]:
        return self.registered_actions[self.callback.action]()
