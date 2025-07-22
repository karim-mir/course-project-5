import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('proj')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-habit-reminders-every-5-minutes': {
        'task': 'habits.tasks.send_habit_reminders',
        'schedule': crontab(minute='*/5'),
    },
}
