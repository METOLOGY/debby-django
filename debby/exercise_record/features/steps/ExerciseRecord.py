# 需要在 runner.py 299行的 open加入 encoding = 'utf-8-sig' 才能正確顯示中文

from behave import *
import urllib.request
from django.apps import apps


@given("a set of {model_name}s in Database")
def step_impl(context, model_name):
    """
    :type context: behave.runner.Context
    """

    model = apps.get_model(*model_name.split('.'))

    for row in context.table:
        model.objects.create(**row.as_dict())

    data = model.objects.first()
    assert data.id == 1

@when("I go to {page_url}")
def step_impl(context, page_url):
    """
    :type context: behave.runner.Context
    """
    #context.response = urllib.request.urlopen(context.test_case.live_server_url + page_url)
    assert False

@then('the return includes "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    :type text: str
    """
    assert False


@step('the return includes "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    assert False
