from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel
from line.callback import MyDiaryCallback
from line.constant import MyDiaryAction as Action
from user.cache import AppCache


class MyDiaryManager(object):
    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback

    def handle(self):
        reply = TextSendMessage(text="ERROR!")
        app_cache = AppCache(self.callback.line_id, app=self.callback.app)

        if self.callback.action == Action.START:
            app_cache.commit()
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
                                                 action=Action.INSULIN_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="用藥紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.DRUG_HISTORY).url
                        )
                    ]
                )

            )
        elif self.callback.action == Action.BG_HISTORY:
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:6]
            if records:
                carousels = []
                    time = record.time.strftime("%H:%M, %x")
                for record in records:
                    type_ = "飯後" if record.type == "after" else "飯前"
                    val = record.glucose_val
                    message = "紀錄時間: {}\n血糖值: {} {}".format(time, type_, val)
                    carousels.append(CarouselColumn(
                        text=message,
                        actions=[
                        PostbackTemplateAction(
                            label='修改記錄',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE,
                                record_pk=records.id).url
                        ),
                        PostbackTemplateAction(
                            label='刪除記錄',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE,
                                record_pk=records.id).url
                        )
                    ]
                ))
            # noinspection PyTypeChecker
            reply = TemplateSendMessage(
                template=CarouselTemplate(
                alt_text="最近的五筆血糖紀錄",
                    columns=carousels
                )
            else:
                reply = TextSendMessage(text="你還沒有記錄過唷, 加把勁記錄血糖吧~")
        elif self.callback.action == Action.YOKATTA:
            reply = TextSendMessage(text="謝謝你的讚美>///<")

        elif self.callback.action == Action.DELETE:
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
                                record_id=self.callback.record_pk).url
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CANCEL,
                                record_id=self.callback.record_pk).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.DELETE_CONFIRM:
            pass

        return reply
