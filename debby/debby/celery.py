from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debby.settings')

app = Celery('debby')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check user setting and push message': {
        'task': 'reminder.tasks.periodic_checking_bg_reminder_setting',
        'schedule': 60
    },
}