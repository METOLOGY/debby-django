import datetime
import os
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel, InsulinIntakeModel, DrugIntakeModel
from food_record.manager import FoodRecordManager
from food_record.models import FoodModel, TempImageModel
from line.callback import MyDiaryCallback, FoodRecordCallback
from line.constant import MyDiaryAction as Action, App, FoodRecordAction
from line.constant import RecordType
from user.cache import AppCache, MyDiaryData


class MyDiaryManager(object):
    @staticmethod
    def confirm_template(line_id, old, new, action, record_id, record_type):
        if isinstance(old, datetime.datetime):
            old_value = old.astimezone().strftime("%Y/%m/%d %H:%M")
            new_value = new.strftime("%Y/%m/%d %H:%M")
        else:
            old_value = old
            new_value = new

        reply = TemplateSendMessage(
            alt_text='您確定要將原本紀錄 {} 修改成 {}?'.format(old_value, new_value),
            template=ButtonsTemplate(
                text='您確定要將原本紀錄 {} 修改成 {}?'.format(old_value, new_value),
                actions=[
                    PostbackTemplateAction(
                        label="是，請修改",
                        data=MyDiaryCallback(line_id=line_id,
                                             action=action,
                                             new_value=new,
                                             record_id=record_id,
                                             record_type=record_type).url
                    ),
                    PostbackTemplateAction(
                        label="否，取消修改",
                        data=MyDiaryCallback(line_id=line_id,
                                             action=Action.UPDATE_CANCEL).url
                    ),
                ]
            )

        )

        return reply

    @staticmethod
    def get_proper_record(record_type, record_id):
        print(record_type, record_id)
        if record_type == RecordType.BG:
            record = BGModel.objects.get(id=record_id)
        elif record_type == RecordType.INSULIN:
            record = InsulinIntakeModel.objects.get(id=record_id)
        elif record_type == RecordType.DRUG:
            record = DrugIntakeModel.objects.get(id=record_id)
        elif record_type == RecordType.FOOD:
            record = FoodModel.objects.get(id=record_id)
        elif record_type == RecordType.TEMP_FOOD:
            record = TempImageModel.objects.get(id=record_id)
        else:
            raise ValueError("shall all included")

        return record

    @staticmethod
    def change_date(val: str, old_datetime: datetime.datetime):
        year = int(val[0:4])
        month = int(val[4:6])
        day = int(val[6:])

        new_date = old_datetime.replace(year=year, month=month, day=day)
        return new_date

    @staticmethod
    def change_time(val: str, old_datetime: datetime.datetime):
        hour = int(val[0:2])
        minute = int(val[2:])

        new_time = old_datetime.replace(hour=hour, minute=minute)
        return new_time

    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback

    @staticmethod
    def no_record() -> TextSendMessage:
        return TextSendMessage(text="抱歉！沒有任何歷史紀錄耶~")

    def is_postprocessing(self):
        if self.callback.record_type == RecordType.TEMP_FOOD:
            return True
        else:
            return False

    def postprocessing(self, app_cache: AppCache):
        if self.callback.record_type == RecordType.TEMP_FOOD:
            app_cache.set_next_action(App.FOOD_RECORD, FoodRecordAction.CHECK_BEFORE_CREATE)
            app_cache.commit()
            callback = self.callback.convert_to(FoodRecordCallback)
            callback.action = FoodRecordAction.CHECK_BEFORE_CREATE
            reply = FoodRecordManager(callback).handle()
            return reply

    def handle(self):
        reply = TextSendMessage(text="MY_DIARY ERROR!")
        app_cache = AppCache(self.callback.line_id)

        if self.callback.action == Action.CREATE_FROM_MENU:
            # init cache again to clean other app's status and data
            app_cache.delete()
            reply = TemplateSendMessage(
                alt_text="請選擇想要檢視的紀錄",
                template=ButtonsTemplate(
                    text="請選擇想要檢視的紀錄",
                    actions=[
                        PostbackTemplateAction(
                            label="血糖紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.BG_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="飲食紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.FOOD_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="用藥紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.DRUG_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="胰島素注射紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.INSULIN_HISTORY).url
                        ),
                    ]
                )
            )
        elif self.callback.action == Action.BG_HISTORY:
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            carousels = []
            record_type = RecordType.BG

            if len(records) == 0:
                reply = self.no_record()
            else:
                for record in records:
                    time = record.time.astimezone().strftime("%H:%M, %x")
                    type_ = "飯後" if record.type == "after" else "飯前"
                    val = record.glucose_val
                    message = "血糖值: {} {}".format(type_, val)
                    carousels.append(CarouselColumn(
                        title="紀錄時間: {}".format(time),
                        text=message,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.BG_UPDATE,
                                    record_type=record_type,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_type=record_type,
                                    record_id=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = [
                    TemplateSendMessage(
                        alt_text="最近的五筆血糖紀錄",
                        template=CarouselTemplate(
                            columns=carousels
                        )
                    ),
                    TextSendMessage("更完整血糖故事請至: http://m.metology.com.tw/")
                ]

        elif self.callback.action == Action.DRUG_HISTORY:
            records = DrugIntakeModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            carousels = []

            if len(records) == 0:
                reply = self.no_record()
            else:
                for record in records:
                    time = record.time.astimezone().strftime("%H:%M, %x")
                    status = "已服用" if record.status else "尚未服用"

                    message = "服用狀況: {}".format(status)
                    carousels.append(CarouselColumn(
                        title="紀錄時間: {}".format(time),
                        text=message,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DRUG_UPDATE,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_type=RecordType.DRUG,
                                    record_id=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = TemplateSendMessage(
                    alt_text="最近的五筆藥物紀錄",
                    template=CarouselTemplate(
                        columns=carousels
                    )
                )

        elif self.callback.action == Action.INSULIN_HISTORY:
            records = InsulinIntakeModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            carousels = []

            if len(records) == 0:
                reply = self.no_record()
            else:
                for record in records:
                    time = record.time.astimezone().strftime("%H:%M, %x")
                    status = "已服用" if record.status else "尚未服用"

                    message = "服用狀況: {}".format(status)
                    carousels.append(CarouselColumn(
                        title="紀錄時間: {}".format(time),
                        text=message,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.INSULIN_UPDATE,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_type=RecordType.INSULIN,
                                    record_id=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = TemplateSendMessage(
                    alt_text="最近的五筆胰島素紀錄",
                    template=CarouselTemplate(
                        columns=carousels
                    )
                )

        elif self.callback.action == Action.FOOD_HISTORY:
            records = FoodModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            carousels = []

            if len(records) == 0:
                reply = self.no_record()
            else:
                for record in records:
                    time = record.time.astimezone().strftime("%H:%M, %x")
                    note = record.note

                    # copy from food_record/manager.py:78
                    host = cache.get("host_name")
                    if record.carousel:
                        url = record.carousel.url
                    else:
                        url = '/media/FoodRecord/default.jpg'

                    photo = "https://{}{}".format(host, url)

                    if record.food_name:
                        message = "食物名稱： {}\n".format(record.food_name) + \
                                  "紀錄內容： {}".format(note)
                    else:
                        message = "紀錄內容： {}".format(note)

                    carousels.append(CarouselColumn(
                        title="紀錄時間: {}".format(time),
                        text=message,
                        thumbnail_image_url=photo,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.FOOD_UPDATE,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_type=RecordType.FOOD,
                                    record_id=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = [
                    TemplateSendMessage(
                        alt_text="最近的五筆飲食紀錄",
                        template=CarouselTemplate(
                            columns=carousels
                        )
                    ),
                    TextSendMessage("更完整血糖故事請至: http://m.metology.com.tw/")
                ]

        elif self.callback.action == Action.DELETE:
            type_ = self.callback.record_type

            reply = TemplateSendMessage(
                alt_text='確定要刪除這筆紀錄？',
                template=ButtonsTemplate(
                    text='您確定要刪除這筆紀錄？',
                    actions=[
                        PostbackTemplateAction(
                            label='確定',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CONFIRM,
                                record_type=type_,
                                record_id=self.callback.record_id).url
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CANCEL,
                                record_type=type_,
                                record_id=self.callback.record_id).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.DELETE_CANCEL:
            action = ''
            if self.callback.record_type == RecordType.BG:
                action = Action.BG_HISTORY

            elif self.callback.record_type == RecordType.INSULIN:
                action = Action.INSULIN_HISTORY

            elif self.callback.record_type == RecordType.DRUG:
                action = Action.DRUG_HISTORY

            self.callback.action = action

            reply = [
                TextSendMessage(text="紀錄仍保留,請選擇欲修改項目"),
                self.handle
            ]

        elif self.callback.action == Action.DELETE_CONFIRM:
            record = self.get_proper_record(record_type=self.callback.record_type, record_id=self.callback.record_id)
            record.delete()

            reply = TextSendMessage(text='刪除成功!')

        elif self.callback.action == Action.BG_UPDATE:
            reply = TemplateSendMessage(
                alt_text="請選擇欲修改的項目",
                template=ButtonsTemplate(
                    text="請選擇欲修改的項目",
                    actions=[
                        PostbackTemplateAction(
                            label="日期",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_DATE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TIME,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="血糖",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_BG_VALUE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="飯前或飯後",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_BG_TYPE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )

        elif self.callback.action == Action.FOOD_UPDATE:
            record_type = RecordType.TEMP_FOOD if self.callback.record_type == RecordType.TEMP_FOOD else RecordType.FOOD
            reply = TemplateSendMessage(
                alt_text="請選擇欲修改的項目",
                template=ButtonsTemplate(
                    text="請選擇欲修改的項目",
                    actions=[
                        PostbackTemplateAction(
                            label="日期",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_DATE,
                                record_type=record_type,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TIME,
                                record_type=record_type,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="照片",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_FOOD_PHOTO,
                                record_type=record_type,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="文字說明",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_FOOD_TEXT,
                                record_type=record_type,
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )

        elif self.callback.action == Action.DRUG_UPDATE:
            reply = TemplateSendMessage(
                alt_text="請選擇欲修改的項目",
                template=ButtonsTemplate(
                    text="請選擇欲修改的項目",
                    actions=[
                        PostbackTemplateAction(
                            label="日期",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_DATE,
                                record_type=RecordType.DRUG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TIME,
                                record_type=RecordType.DRUG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )

        elif self.callback.action == Action.INSULIN_UPDATE:
            reply = TemplateSendMessage(
                alt_text="請選擇欲修改的項目",
                template=ButtonsTemplate(
                    text="請選擇欲修改的項目",
                    actions=[
                        PostbackTemplateAction(
                            label="日期",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_DATE,
                                record_type=RecordType.INSULIN,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TIME,
                                record_type=RecordType.INSULIN,
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_DATE:
            app_cache.set_next_action(self.callback.app, Action.UPDATE_DATE_CHECK)
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請輸入西元年月日共8碼,例如: 20170225",
                template=ButtonsTemplate(
                    text="請輸入西元年月日共8碼,例如: 20170225",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_TIME:
            app_cache.set_next_action(self.callback.app, Action.UPDATE_TIME_CHECK)
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請輸入時間共4碼,例如晚上七點半: 1930",
                template=ButtonsTemplate(
                    text="請輸入時間共4碼,例如晚上七點半: 1930",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_BG_VALUE:
            app_cache.set_next_action(self.callback.app, Action.UPDATE_BG_VALUE_CHECK)
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請輸入血糖值",
                template=ButtonsTemplate(
                    text="請輸入血糖值",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_BG_TYPE:
            old_type = BGModel.objects.get(id=self.callback.record_id).type
            if old_type == 'before':
                new_type = 'after'
            else:
                new_type = 'before'

            type_to_chinese = {'before': '飯前', 'after': '飯後'}

            reply = self.confirm_template(
                line_id=self.callback.line_id,
                old=type_to_chinese[old_type],
                new=type_to_chinese[new_type],
                action=Action.UPDATE_BG_TYPE_CONFIRM,
                record_id=self.callback.record_id,
                record_type=self.callback.record_type
            )

        elif self.callback.action == Action.UPDATE_DATE_CHECK:
            text = self.callback.text
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)

            try:
                new_date = self.change_date(text, record.time)
                data = app_cache.data
                data.new_datetime = new_date
                app_cache.save_data(data)

                reply = self.confirm_template(
                    line_id=app_cache.line_id,
                    old=record.time,
                    new=new_date,
                    action=Action.UPDATE_DATE_CONFIRM,
                    record_id=record_id,
                    record_type=record_type
                )

            except ValueError:
                app_cache.delete()
                reply = TemplateSendMessage(
                    alt_text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                    template=ButtonsTemplate(
                        text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_DATE,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )

        elif self.callback.action == Action.UPDATE_TIME_CHECK:
            text = self.callback.text
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)

            try:
                new_date = self.change_time(text, record.time)
                reply = self.confirm_template(
                    line_id=app_cache.line_id,
                    old=record.time,
                    new=new_date,
                    action=Action.UPDATE_TIME_CONFIRM,
                    record_type=record_type,
                    record_id=record_id
                )

            except ValueError:
                app_cache.delete()
                reply = TemplateSendMessage(
                    alt_text="哎呀！您如果要修改時間的話請依照格式輸入喔！",
                    template=ButtonsTemplate(
                        text="哎呀！您如果要修改時間的話請依照格式輸入喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_TIME,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )

        elif self.callback.action == Action.UPDATE_BG_VALUE_CHECK:
            text = self.callback.text
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)

            if text.isdigit():
                new_value = int(text)

                reply = self.confirm_template(
                    line_id=app_cache.line_id,
                    old=record.glucose_val,
                    new=new_value,
                    action=Action.UPDATE_BG_VALUE_CONFIRM,
                    record_type=record_type,
                    record_id=record_id
                )
            else:
                app_cache.delete()
                reply = TemplateSendMessage(
                    alt_text="哎呀！您如果要修改血糖的話請輸入數字喔！",
                    template=ButtonsTemplate(
                        text="哎呀！您如果要修改血糖的話請輸入數字喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_BG_VALUE,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )
        elif self.callback.action == Action.UPDATE_DATE_CONFIRM or self.callback.action == Action.UPDATE_TIME_CONFIRM:
            record_type = self.callback.record_type
            record_id = self.callback.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)
            record.time = self.callback.new_value
            record.save()

            if self.is_postprocessing():
                reply = self.postprocessing(app_cache)
            else:
                reply = TextSendMessage(text="修改成功!")
                app_cache.delete()

        elif self.callback.action == Action.UPDATE_BG_VALUE_CONFIRM:
            record_type = self.callback.record_type
            record_id = self.callback.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)
            record.glucose_val = self.callback.new_value
            record.save()

            reply = TextSendMessage(text="修改成功!")
            app_cache.delete()

        elif self.callback.action == Action.UPDATE_BG_TYPE_CONFIRM:
            chinese_to_type = {'飯前': 'before', '飯後': 'after'}

            record_type = self.callback.record_type
            record_id = self.callback.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)
            record.type = chinese_to_type[self.callback.new_value]
            record.save()

            reply = TextSendMessage(text="修改成功!")
            app_cache.delete()

        elif self.callback.action == Action.UPDATE_FOOD_TEXT:
            app_cache.set_next_action(self.callback.app, Action.UPDATE_FOOD_TEXT_CHECK)
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請輸入新的文字紀錄",
                template=ButtonsTemplate(
                    text="請輸入新的文字紀錄",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_FOOD_TEXT_CHECK:
            text = self.callback.text
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)

            if text == '' or text is None:
                reply = TemplateSendMessage(
                    alt_text="哎呀！請您輸入文字說明才能修改紀錄喔！",
                    template=ButtonsTemplate(
                        text="哎呀！請您輸入文字說明才能修改紀錄喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_FOOD_TEXT,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )

            else:
                data = app_cache.data
                data.text = text
                app_cache.save_data(data)

                reply = self.confirm_template(
                    line_id=app_cache.line_id,
                    old=record.note,
                    new=text,
                    action=Action.UPDATE_FOOD_TEXT_CONFIRM,
                    record_id=record_id,
                    record_type=record_type
                )

        elif self.callback.action == Action.UPDATE_FOOD_TEXT_CONFIRM:
            record_type = self.callback.record_type
            record_id = self.callback.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)
            record.note = app_cache.data.text
            record.save()

            if self.is_postprocessing():
                reply = self.postprocessing(app_cache)
            else:
                reply = TextSendMessage(text="修改成功!")
                app_cache.delete()

        elif self.callback.action == Action.UPDATE_FOOD_PHOTO:
            app_cache.set_next_action(self.callback.app, Action.UPDATE_FOOD_PHOTO_CHECK)
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請重新上傳一張新的影像",
                template=ButtonsTemplate(
                    text="請重新上傳一張新的影像",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_FOOD_PHOTO_CHECK:
            text = self.callback.text
            image_id = self.callback.image_id
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)

            if (text != '' or text is not None) and not image_id:
                reply = TemplateSendMessage(
                    alt_text="哎呀！請您上傳圖片才能修改紀錄喔！",
                    template=ButtonsTemplate(
                        text="哎呀！請您上傳圖片才能修改紀錄喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新上傳",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_FOOD_PHOTO,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )
            else:
                image_id = self.callback.image_id
                message_content = settings.LINE_BOT_API.get_message_content(message_id=image_id)
                image = message_content.content
                if not record.food_image_upload.name:
                    file = '{0}_food_image.jpg'.format(self.callback.line_id)
                    record.food_image_upload.save(file, File(BytesIO(image)))
                else:
                    ori_filename = os.path.basename(record.food_image_upload.name)
                    record.food_image_upload.save('updated_' + ori_filename, File(BytesIO(image)))
                record.save()
                record.make_carousel()

                if self.is_postprocessing():
                    reply = self.postprocessing(app_cache)
                else:
                    reply = TextSendMessage(text="修改成功!")
                    app_cache.delete()

        elif self.callback.action == Action.UPDATE_CANCEL:
            reply = TextSendMessage(text="好的！那就不更動您原始的紀錄囉！")
            app_cache.delete()

        return reply
