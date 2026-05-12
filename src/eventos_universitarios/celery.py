from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventos_universitarios.settings')

app = Celery('eventos_universitarios')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()