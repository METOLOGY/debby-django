# reference https://anvileight.com/blog/2016/04/12/behavior-driven-development-pycharm-python-django/
import os
import django
from behave.model import Scenario
from behave.runner import Context
from django.test.runner import DiscoverRunner
from django.test.testcases import LiveServerTestCase

os.environ['DJANGO_SETTINGS_MODULE'] = 'debby.settings'
django.setup()


def before_all(context: Context):
    context.test_runner = DiscoverRunner()
    context.test_runner.setup_test_environment()
    context.old_db_config = context.test_runner.setup_databases()


def after_all(context: Context):
    context.test_runner.teardown_databases(context.old_db_config)
    context.test_runner.teardown_test_environment()


def before_scenario(context: Context, scenario: Scenario):
    context.test_case = LiveServerTestCase
    context.test_case.setUpClass()


def after_scenario(context: Context, scenario: Scenario):
    context.test_case.tearDownClass()
    del context.test_case
