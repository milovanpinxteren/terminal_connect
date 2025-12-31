from django.urls import path
from . import views
from .mock_views import *

urlpatterns = [
    path('start', views.start_transaction, name='start_transaction'),
    path('status', views.get_transaction_status, name='get_transaction_status'),

    path('mock/start', mock_start_transaction),
    path('mock/start-fail', mock_start_failed),  # fails after 3s
    path('mock/start-timeout', mock_start_timeout),
    path('mock/status', mock_get_transaction_status),
]
