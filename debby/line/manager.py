from linebot.models import TemplateSendMessage, ButtonsTemplate, TextSendMessage, PostbackTemplateAction, \
    URITemplateAction, MessageTemplateAction, CarouselTemplate, CarouselColumn

from line.callback import DrugAskCallback, ConsultFoodCallback, MyDiaryCallback, UserSettingsCallback
from line.callback import LineCallback, BGRecordCallback, FoodRecordCallback
from line.constant import DrugAskAction, ConsultFoodAction
from line.constant import LineAction, BGRecordAction, FoodRecordAction, MyDiaryAction, UserSettingsAction


class LineManager(object):
    def __init__(self, callback: LineCallback):
        self.callback = callback

    def handle(self):
        reply = TextSendMessage(text='ERROR!')

        if self.callback.action == LineAction.MAIN_START:
            carousels = []

            # the record part
            carousels.append(CarouselColumn(
                title="記錄生活",
                text="請選擇要記錄的項目",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/record.png',
                actions=[
                    PostbackTemplateAction(
                        label='記錄血糖',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=BGRecordAction.CREATE_FROM_MENU,
                            text=self.callback.text
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='記錄飲食',
                        data=FoodRecordCallback(
                            line_id=self.callback.line_id,
                            action=FoodRecordAction.CREATE_FROM_MENU,
                        ).url
                    ),
                    # PostbackTemplateAction(
                    #     label='服用藥物',
                    #     data=BGRecordCallback(
                    #         line_id=self.callback.line_id,
                    #         action=BGRecordAction.CREATE_DRUG_RECORD
                    #     ).url
                    # ),
                    # PostbackTemplateAction(
                    #     label='注射胰島素',
                    #     data=BGRecordCallback(
                    #         line_id=self.callback.line_id,
                    #         action=BGRecordAction.CREATE_INSULIN_RECORD
                    #     ).url
                    # ),
                ]
            ))

            # the search part
            carousels.append(CarouselColumn(
                title="搜尋相關資訊",
                text="請選擇要搜尋的項目",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/search.png',
                actions=[
                    PostbackTemplateAction(
                        label='藥物查詢',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=DrugAskAction.READ_FROM_MENU
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='食物營養成份查詢',
                        data=ConsultFoodCallback(
                            line_id=self.callback.line_id,
                            action=ConsultFoodAction.READ_FROM_MENU
                        ).url
                    )
                ]
            ))

            # the diary part
            carousels.append(CarouselColumn(
                title="我的日記",
                text="請選擇要檢視的記錄項目（最多五筆）",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/summary.png',
                actions=[
                    PostbackTemplateAction(
                        label="血糖紀錄",
                        data=MyDiaryCallback(line_id=self.callback.line_id,
                                             action=MyDiaryAction.BG_HISTORY).url
                    ),
                    PostbackTemplateAction(
                        label="飲食紀錄",
                        data=MyDiaryCallback(line_id=self.callback.line_id,
                                             action=MyDiaryAction.FOOD_HISTORY).url
                    ),
                ]
            ))

            # the reminder part
            carousels.append(CarouselColumn(
                title="用藥提醒",
                text="請選擇要設定的提醒項目",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/reminder.png',
                actions=[
                    PostbackTemplateAction(
                        label='服用藥物',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=UserSettingsAction.SET_REMINDER,
                                                  choice='drug').url
                    ),
                    PostbackTemplateAction(
                        label='量測血糖',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=UserSettingsAction.SET_REMINDER,
                                                  choice='bg').url
                    ),
                ]
            ))

            # the reminder part
            text = "您好！我的名字是Debby \uD83D\uDE0A 我是一位線上虛擬營養衛教師 \uD83D\uDE06 希望可以幫助您管理日常生活中的大小事哦！您可於下方主選單內選擇:\n" \
                   "(1) 記錄生活: 可快速記錄血糖值或飲食內容，跟著Debby我的步驟來完成吧！\n" \
                   "(2) 搜尋相關資訊: 如果您想瞭解食物的營養組成成分，我會依據六大類均衡原則，建議最適合您的攝取量哦！您也可以搜尋糖尿病用藥哦！\n" \
                   "(3) 我的日記: 您還可即時查詢最近五筆血糖或飲食的紀錄情形，也可以再修改喔!\n" \
                   "(詳細報表: http://m.metology.com.tw/)\n" \
                   "(4) 用藥提醒:不要害怕忘記自己要吃藥或量血糖～由我來提醒您時間吧，請放心！\n" \
                   "(5) 生活超市(尚未營運): 交給Debby我及專業醫師與營養師嚴格篩選，給您最棒最優質的產品，放心享用去～\n" \
                   "(商城平台: https://jasonli5467684.shoplineapp.com/)\n" \
                   "您也可以在訊息欄內直接輸入您想跟我說的話哦！" \
                   "(例如數字,食物名稱,藥物名稱,或直接上傳照片)，會發現意想不到的驚喜喔^^"
            carousels.append(CarouselColumn(
                title="其他",
                text="更完整的互動介面！挑選Debby推薦的飲食來源！",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/shop.png',
                actions=[
                    MessageTemplateAction(
                        label='如何使用Debby?',
                        text=text
                    ),
                    URITemplateAction(
                        label='Metology商城(尚未營運)',
                        uri='https://jasonli5467684.shoplineapp.com/'
                    ),
                ]
            ))

            # noinspection PyTypeChecker
            reply = [TemplateSendMessage(
                alt_text='Debby says...',
                template=CarouselTemplate(
                    columns=carousels
                )
            ), TextSendMessage(text="更完整血糖故事請至: http://m.metology.com.tw/")]

        if self.callback.action == LineAction.RECORD_START:
            reply = TemplateSendMessage(
                alt_text='請問您要紀錄的是？',
                template=ButtonsTemplate(
                    text='請問您要紀錄的是？',
                    actions=[
                        PostbackTemplateAction(
                            label='記錄血糖',
                            data=BGRecordCallback(
                                line_id=self.callback.line_id,
                                action=BGRecordAction.CREATE_FROM_MENU,
                                text=self.callback.text
                            ).url
                        ),
                        PostbackTemplateAction(
                            label='記錄飲食',
                            data=FoodRecordCallback(
                                line_id=self.callback.line_id,
                                action=FoodRecordAction.CREATE_FROM_MENU,
                            ).url
                        ),
                        PostbackTemplateAction(
                            label='服用藥物',
                            data=BGRecordCallback(
                                line_id=self.callback.line_id,
                                action=BGRecordAction.CREATE_DRUG_RECORD
                            ).url
                        ),
                        PostbackTemplateAction(
                            label='注射胰島素',
                            data=BGRecordCallback(
                                line_id=self.callback.line_id,
                                action=BGRecordAction.CREATE_INSULIN_RECORD
                            ).url
                        ),

                    ]
                )
            )

        elif self.callback.action == LineAction.CONSULT_START:
            reply = TemplateSendMessage(
                alt_text='請問您要查詢的是？',
                template=ButtonsTemplate(
                    text='請問您要查詢的是？',
                    actions=[
                        PostbackTemplateAction(
                            label='藥物查詢',
                            data=DrugAskCallback(
                                line_id=self.callback.line_id,
                                action=DrugAskAction.READ_FROM_MENU
                            ).url
                        ),
                        PostbackTemplateAction(
                            label='食物營養成分查詢',
                            data=ConsultFoodCallback(
                                line_id=self.callback.line_id,
                                action=ConsultFoodAction.READ_FROM_MENU
                            ).url
                        )
                    ]
                )
            )

        return reply
