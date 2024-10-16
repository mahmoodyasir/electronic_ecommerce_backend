# your_project/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electronic_ecommerce_backend.settings')

app = Celery('electronic_ecommerce_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
