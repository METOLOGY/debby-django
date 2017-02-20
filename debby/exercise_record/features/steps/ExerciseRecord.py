# 需要在 runner.py 299行的 open加入 encoding = 'utf-8-sig' 才能正確顯示中文

from behave import *
import urllib.request


@given("a set of {model_name}s in Database")
def step_impl(context, model_name):
    """
    :type context: behave.runner.Context
    """
    pass


@when("I go to {page_url}")
def step_impl(context, page_url):
    """
    :type context: behave.runner.Context
    """
    context.response = urllib.request.urlopen(context.test_case.live_server_url + page_url)


@then('the return includes "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    :type text: str
    """
    pass


@step('the return includes "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    assert False
