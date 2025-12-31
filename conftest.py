import pytest
import os
import django
from django.conf import settings


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure Django database for testing"""
    pass


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests"""
    pass
