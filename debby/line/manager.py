from linebot.models import TemplateSendMessage, ButtonsTemplate, TextSendMessage, PostbackTemplateAction, URITemplateAction, MessageTemplateAction, CarouselTemplate, CarouselColumn
from line.callback import LineCallback, BGRecordCallback, FoodRecordCallback
from line.callback import DrugAskCallback, ConsultFoodCallback, MyDiaryCallback, UserSettingsCallback
from user.cache import AppCache
from line.constant import LineAction, BGRecordAction, FoodRecordAction, MyDiaryAction, UserSettingsAction
from line.constant import DrugAskAction, ConsultFoodAction


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
                        label='食物營養成分查詢',
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
            carousels.append(CarouselColumn(
                title="生活市集",
                text="更完整的互動介面！挑選Debby推薦的飲食來源！",
                thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/shop.png',
                actions=[
                    URITemplateAction(
                        label='血糖故事',
                        uri='http://m.metology.com.tw/'
                    ),
                    URITemplateAction(
                        label='Metology商城',
                        uri='https://jasonli5467684.shoplineapp.com/'
                    ),
                ]
            ))

            # noinspection PyTypeChecker
            reply = TemplateSendMessage(
                alt_text='Debby says...',
                template=CarouselTemplate(
                    columns=carousels
                )
            )

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
