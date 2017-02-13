from behave import *

use_step_matcher("re")


@given("a set of Exercise in Database")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@when("I go to /exercise/")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@then('the return includes "跑步"')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@step('the return includes "散步"')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass
