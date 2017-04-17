from django.db.models import QuerySet
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction
from linebot.models import TextSendMessage

from drug_ask.models import DrugTypeModel, DrugDetailModel
from line.callback import DrugAskCallback
from user.cache import AppCache, DrugAskData


class DrugAskManager(object):
    def __init__(self, callback: DrugAskCallback):
        self.callback = callback

    @staticmethod
    def reply_choose_one(drug_types: QuerySet) -> TextSendMessage:
        choice_texts = ""
        for drug_type in drug_types:  # type: DrugTypeModel
            choice_texts += drug_type.user_choice + "\n"
        message = "請選擇符合的項目:\n"
        return TextSendMessage(text=message + choice_texts)

    @staticmethod
    def reply_want_which_content(drug_detail: DrugDetailModel) -> TemplateSendMessage:
        message = drug_detail.type + "\n" + "請問您要查詢什麼項目呢?"
        reply = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label='(1) 作用機轉和服用方式',
                        data='app=DrugAsk&action=READ_DRUG_DETAIL&choice=1'
                    ),
                    PostbackTemplateAction(
                        label='(2) 不良反應,副作用',
                        data='app=DrugAsk&action=READ_DRUG_DETAIL&choice=2'
                    ),
                    PostbackTemplateAction(
                        label='(3) 禁忌',
                        data='app=DrugAsk&action=READ_DRUG_DETAIL&choice=3'
                    ),
                    PostbackTemplateAction(
                        label='(4) 注意事項',
                        data='app=DrugAsk&action=READ_DRUG_DETAIL&choice=4'
                    )
                ]
            )
        )
        return reply

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app='DrugAsk')

        if self.callback.action == 'READ_FROM_MENU':
            app_cache.set_next_action(action="READ")
            app_cache.commit()

            reply = TextSendMessage(text="請輸入藥品名稱(中英文皆可):")
        elif self.callback.action == 'READ':
            drug_types = DrugTypeModel.objects.filter(question=self.callback.text)
            if len(drug_types) > 1:
                app_cache.set_next_action(action="WAIT_DRUG_TYPE_CHOICE")

                data = DrugAskData()
                data.drug_types = drug_types
                app_cache.save_data(data)

                reply = self.reply_choose_one(drug_types)
            elif len(drug_types) == 1:
                drug_type = drug_types[0]
                drug_detail = DrugDetailModel.objects.get(type=drug_type.type)

                data = DrugAskData()
                data.drug_detail_pk = drug_detail.pk
                app_cache.save_data(data)
                reply = self.reply_want_which_content(drug_detail)
            else:
                reply = TextSendMessage(text="ERROR!")
        elif self.callback.action == 'WAIT_DRUG_TYPE_CHOICE':
            if not self.callback.text.isdigit():
                reply = TextSendMessage(text="請輸入選項中的數字喔~")
            else:
                if app_cache.is_app_running():
                    data = app_cache.data  # type: DrugAskData
                    drug_types = data.drug_types

                    drug_type = drug_types.get(user_choice__startswith=self.callback.text)  # type: DrugTypeModel
                    drug_detail = DrugDetailModel.objects.get(type=drug_type.type)

                    data = DrugAskData()
                    data.drug_detail_pk = drug_detail.pk
                    app_cache.save_data(data)
                    reply = self.reply_want_which_content(drug_detail)
                else:
                    print('Error!')
        elif self.callback.action == "READ_DRUG_DETAIL":
            data = app_cache.data  # type: DrugAskData
            message = "偷偷跟你說, Debby忘記你問甚麼了><, 可以重新問我一遍嗎~"
            if data:
                drug_detail_pk = data.drug_detail_pk

                drug_detail = DrugDetailModel.objects.get(pk=drug_detail_pk)
                message = "Error!"
                if self.callback.choice == "1":
                    message = "1.作用機轉和服用方式\n" + drug_detail.mechanism
                elif self.callback.choice == "2":
                    message = "2.不良反應,副作用\n" + drug_detail.side_effect
                elif self.callback.choice == "3":
                    message = "3.禁忌\n" + drug_detail.taboo
                elif self.callback.choice == "4":
                    message = "4.注意事項\n" + drug_detail.awareness

            reply = TextSendMessage(text=message)

        return reply
