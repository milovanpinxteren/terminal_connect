from django.urls import path
from .mock_views import *
from .views.shopify_webhook_views import *
from .views.views import get_transaction_status, start_transaction, app_home, get_transactions

urlpatterns = [
    # Embedded app UI
    path('app/', app_home, name='app_home'),
    path('transactions/', get_transactions, name='get_transactions'),

    # POS extension endpoints
    path('start', start_transaction, name='start_transaction'),
    path('status', get_transaction_status, name='get_transaction_status'),

    # Mock endpoints for testing
    path('mock/start', mock_start_transaction),
    path('mock/start-fail', mock_start_failed),
    path('mock/start-timeout', mock_start_timeout),
    path('mock/status', mock_get_transaction_status),

    # Shopify webhooks
    path('webhooks', shopify_webhook, name='shopify_webhook'),
]