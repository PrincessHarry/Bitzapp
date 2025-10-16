from django.urls import path

from .webhook import bitnob_webhook

urlpatterns = [
    path('bitnob/webhook/', bitnob_webhook, name='bitnob-webhook'),
]


