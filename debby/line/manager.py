from linebot.models import TemplateSendMessage, ButtonsTemplate, TextSendMessage, PostbackTemplateAction
from line.callback import LineCallback, BGRecordCallback, FoodRecordCallback
from line.callback import DrugAskCallback, ConsultFoodCallback
from user.cache import AppCache
from line.constant import LineAction, BGRecordAction, FoodRecordAction
from line.constant import DrugAskAction, ConsultFoodAction


class LineManager(object):
    def __init__(self, callback: LineCallback):
        self.callback = callback

    def handle(self):
        reply = TextSendMessage(text='ERROR!')

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
