from django.urls import path
from .mock_views import *
from .views.shopify_webhook_views import *
from .views.views import get_transaction_status, start_transaction

urlpatterns = [
    path('start', start_transaction, name='start_transaction'),
    path('status', get_transaction_status, name='get_transaction_status'),
    path('mock/start', mock_start_transaction),
    path('mock/start-fail', mock_start_failed),  # fails after 3s
    path('mock/start-timeout', mock_start_timeout),
    path('mock/status', mock_get_transaction_status),

    path('webhooks', shopify_webhSook, name='shopify_webhook'),

]
