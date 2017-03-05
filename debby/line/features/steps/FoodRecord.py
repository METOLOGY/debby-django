from behave import *


from django.apps import apps


@when('我點擊了選單 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    :type text: str
    """
    context.ih = InputHandler(text)


@then('他會回傳 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    :type text: str
    """
    assert context.ih.reply_to_input() == text
