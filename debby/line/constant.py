class App(object):
    BG_RECORD = 'BGRecord'
    CHAT = 'Chat'
    CONSULT_FOOD = 'ConsultFood'
    DRUG_ASK = 'DrugAsk'
    FOOD_RECORD = 'FoodRecord'
    MY_DIARY = 'MyDiary'
    REMINDER = 'Reminder'


class Action(object):
    pass


class BGRecordAction(Action):
    CONFIRM_RECORD = 'CONFIRM_RECORD'
    CREATE_FROM_MENU = 'CREATE_FROM_MENU'
    CREATE_FROM_VALUE = 'CREATE_FROM_VALUE'
    SET_TYPE = 'SET_TYPE'


class ConsultFoodAction(Action):
    READ_FROM_MENU = 'READ_FROM_MENU'


class DrugAskAction(Action):
    READ = 'READ'
    READ_DRUG_DETAIL = 'READ_DRUG_DETAIL'
    READ_FROM_MENU = 'READ_FROM_MENU'
    WAIT_DRUG_TYPE_CHOICE = 'WAIT_DRUG_TYPE_CHOICE'


class FoodRecordAction(Action):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    CANCEL = 'CANCEL'

    CREATE_FROM_MENU = 'CREATE_FROM_MENU'
    DIRECT_UPLOAD_IMAGE = 'DIRECT_UPLOAD_IMAGE'
    MODIFY_EXTRA_INFO = 'MODIFY_EXTRA_INFO'
    WAIT_FOR_USER_REPLY = 'WAIT_FOR_USER_REPLY'


class MyDiaryAction(Action):
    START = 'START'
    BG_HISTORY = 'BG_HISTORY'
    YOKATTA = 'YOKATTA'


class ReminderAction(Action):
    REPLY_REMINDER = 'REPLY_REMINDER'