import pytest
from django.utils import timezone
from terminal.models import TerminalLinks, Transaction


@pytest.mark.django_db
class TestTerminalLinks:
    """Test TerminalLinks model"""

    def test_create_terminal_link(self):
        """Test creating a terminal link"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='test-api-key',
            location_id='loc-123',
            staff_member_id='staff-456'
        )
        assert terminal.shop_domain == 'test.myshopify.com'
        assert terminal.terminal_id == '12345'
        assert terminal.api_key == 'test-api-key'
        assert terminal.location_id == 'loc-123'
        assert terminal.staff_member_id == 'staff-456'
        assert terminal.created_at is not None
        assert terminal.updated_at is not None

    def test_terminal_link_str(self):
        """Test string representation of terminal link"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='test-api-key'
        )
        assert str(terminal) == 'test.myshopify.com -> 12345'

    def test_terminal_link_with_optional_fields(self):
        """Test creating terminal link with all optional fields"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='test-api-key',
            shop_id='shop-123',
            user_id='user-456',
            location_id='loc-789',
            staff_member_id='staff-012'
        )
        assert terminal.shop_id == 'shop-123'
        assert terminal.user_id == 'user-456'


@pytest.mark.django_db
class TestTransaction:
    """Test Transaction model"""

    def test_create_transaction(self):
        """Test creating a transaction"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='test-api-key'
        )

        transaction = Transaction.objects.create(
            transaction_id='txn-123',
            terminal_link=terminal,
            amount=1000,
            status='started',
            shop_domain='test.myshopify.com'
        )

        assert transaction.transaction_id == 'txn-123'
        assert transaction.terminal_link == terminal
        assert transaction.amount == 1000
        assert transaction.status == 'started'
        assert transaction.shop_domain == 'test.myshopify.com'
        assert transaction.created_at is not None

    def test_transaction_str(self):
        """Test string representation of transaction"""
        transaction = Transaction.objects.create(
            transaction_id='txn-123',
            amount=1000,
            status='success',
            shop_domain='test.myshopify.com'
        )
        assert str(transaction) == 'txn-123 - success'

    def test_transaction_status_update(self):
        """Test updating transaction status"""
        transaction = Transaction.objects.create(
            transaction_id='txn-123',
            amount=1000,
            status='started',
            shop_domain='test.myshopify.com'
        )

        transaction.status = 'success'
        transaction.receipt = 'Receipt data...'
        transaction.save()

        transaction.refresh_from_db()
        assert transaction.status == 'success'
        assert transaction.receipt == 'Receipt data...'

    def test_transaction_with_error(self):
        """Test transaction with error message"""
        transaction = Transaction.objects.create(
            transaction_id='txn-123',
            amount=1000,
            status='failed',
            error_msg='Card declined',
            shop_domain='test.myshopify.com'
        )
        assert transaction.status == 'failed'
        assert transaction.error_msg == 'Card declined'

    def test_transaction_status_choices(self):
        """Test all valid status choices"""
        valid_statuses = ['started', 'success', 'failed', 'timeout']

        for status in valid_statuses:
            transaction = Transaction.objects.create(
                transaction_id=f'txn-{status}',
                amount=1000,
                status=status,
                shop_domain='test.myshopify.com'
            )
            assert transaction.status == status
