class App(object):
    BG_RECORD = 'BGRecord'
    CHAT = 'Chat'
    CONSULT_FOOD = 'ConsultFood'
    DRUG_ASK = 'DrugAsk'
    FOOD_RECORD = 'FoodRecord'
    MY_DIARY = 'MyDiary'
    REMINDER = 'Reminder'
    LINE = 'LINE'
    USER_SETTING = 'UserSetting'


class Action(object):
    pass


class BGRecordAction(Action):
    CONFIRM_RECORD = 'CONFIRM_RECORD'
    CREATE_FROM_MENU = 'CREATE_FROM_MENU'
    CREATE_FROM_VALUE = 'CREATE_FROM_VALUE'
    SET_TYPE = 'SET_TYPE'

    CREATE_DRUG_RECORD = 'CREATE_DRUG_RECORD'
    CREATE_DRUG_RECORD_CONFIRM = 'CREATE_DRUG_RECORD_CONFIRM'
    CREATE_DRUG_RECORD_CANCEL = 'CREATE_DRUG_RECORD_CANCEL'
    CREATE_INSULIN_RECORD = 'CREATE_INSULIN_RECORD'
    CREATE_INSULIN_RECORD_CONFIRM = 'CREATE_INSULIN_RECORD_CONFIRM'
    CREATE_INSULIN_RECORD_CANCEL = 'CREATE_INSULIN_RECORD_CANCEL'

class ConsultFoodAction(Action):
    READ = 'READ'
    READ_FROM_MENU = 'READ_FROM_MENU'
    WAIT_FOOD_NAME_CHOICE = 'WAIT_FOOD_NAME_CHOICE'


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
    CHECK_BEFORE_CREATE = 'CHECK_BEFORE_CREATE'


class MyDiaryAction(Action):
    CREATE_FROM_MENU = 'CREATE_FROM_MENU'
    BG_HISTORY = 'BG_HISTORY'
    INSULIN_HISTORY = 'INSULIN_HISTORY'
    DRUG_HISTORY = 'DRUG_HISTORY'
    FOOD_HISTORY = 'FOOD_HISTORY'

    BG_UPDATE = 'BG_UPDATE'
    DRUG_UPDATE = 'DRUG_UPDATE'
    INSULIN_UPDATE = 'INSULIN_UPDATE'
    UPDATE_DATE = 'UPDATE_DATE'
    UPDATE_TIME = 'UPDATE_TIME'

    UPDATE_DATE_CHECK = 'UPDATE_DATE_CHECK'
    UPDATE_DATE_CONFIRM = 'UPDATE_DATE_CONFIRM'
    UPDATE_TIME_CHECK = 'UPDATE_TIME_CHECK'
    UPDATE_TIME_CONFIRM = 'UPDATE_TIME_CONFIRM'

    UPDATE_BG_VALUE = 'UPDATE_BG_VALUE'
    UPDATE_BG_VALUE_CHECK = 'UPDATE_BG_VALUE_CHECK'
    UPDATE_BG_VALUE_CONFIRM = 'UPDATE_BG_VALUE_CONFIRM'

    UPDATE_BG_TYPE = 'UPDATE_BG_TYPE'
    UPDATE_BG_TYPE_CONFIRM = 'UPDATE_BG_TYPE_CONFIRM'

    UPDATE_FOOD_VALUE = 'UPDATE_FOOD_VALUE'

    UPDATE_CANCEL = 'UPDATE_CANCEL'

    DELETE = 'DELETE'
    DELETE_CONFIRM = 'DELETE_CONFIRM'
    DELETE_CANCEL = 'DELETE_CANCEL'


class ReminderAction(Action):
    REPLY_REMINDER = 'REPLY_REMINDER'


class RecordType(object):
    BG = 'BG'
    INSULIN = 'INSULIN'
    DRUG = 'DRUG'
    FOOD = 'FOOD'


class UserSettingsAction(Action):
    CREATE_FROM_MENU = 'CREATE_FROM_MENU'
    SELECT_UNIT = 'SELECT_UNIT'
    SELECT_REMINDED_TYPE = 'SELECT_REMINDED_TYPE'

    SET_UNIT = 'SET_UNIT'

    SET_REMINDER = 'SET_REMINDER'

    SET_REMINDER_TIME = 'SET_REMINDER_TIME'

    TURN_OFF_REMINDER = 'TURN_OFF_REMINDER'
    CONFIRM_TURN_OFF_REMINDER = 'CONFIRM_TURN_OFF_REMINDER'
    CHECK_INPUT_REMINDER_TIME = 'CHECK_INPUT_REMINDER_TIME'

    END_CONVERSATION = 'END_CONVERSATION'

class LineAction(Action):
    RECORD_START = 'RECORD_START'
    CONSULT_START = 'CONSULT_START'
