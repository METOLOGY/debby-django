## celery-beat

follow the construction of django-celery-beat set up steps
http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#using-custom-scheduler-classes

1. initiate with celery-beat custom scheduler

    `celery -A debby beat -l info -S django`

2. initiate celery worker

    `celery -A debby worker --loglevel=info`

3. Then edit the periodic tasks in admin panel.

> notice that, celery worker and scheduler are totally different.
> I recommend to use this extension because it is much easier to setup periodic tasks.