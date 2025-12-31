import json
import pytest
import responses
from django.test import Client
from terminal.models import TerminalLinks, Transaction


@pytest.fixture
def client():
    """Create Django test client"""
    return Client()


@pytest.fixture
def terminal():
    """Create a test terminal link"""
    return TerminalLinks.objects.create(
        shop_domain='test.myshopify.com',
        terminal_id='50303253',
        api_key='test-api-key',
        location_id='loc-123'
    )


@pytest.mark.django_db
class TestStartTransactionView:
    """Test start_transaction view"""

    @responses.activate
    def test_start_transaction_success(self, client, terminal):
        """Test successful transaction start"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/start',
            json={
                'transactionId': '2405102',
                'status': 'started',
                'amount': 1250,
                'terminal': '50303253',
                'createdAt': '2022-06-25 17:10:36'
            },
            status=200
        )

        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'locationId': 'loc-123',
                'amount': 1250
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['transaction_id'] == '2405102'
        assert data['status'] == 'started'

        # Verify transaction was created in database
        transaction = Transaction.objects.get(transaction_id='2405102')
        assert transaction.amount == 1250
        assert transaction.status == 'started'
        assert transaction.shop_domain == 'test.myshopify.com'

    def test_start_transaction_missing_shop_domain(self, client):
        """Test transaction start with missing shopDomain"""
        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'amount': 1250
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'shopDomain is required' in data['error']

    def test_start_transaction_missing_amount(self, client, terminal):
        """Test transaction start with missing amount"""
        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'amount is required' in data['error']

    def test_start_transaction_invalid_amount(self, client, terminal):
        """Test transaction start with invalid amount"""
        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'amount': 'not-a-number'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'amount must be an integer' in data['error']

    def test_start_transaction_invalid_json(self, client):
        """Test transaction start with invalid JSON"""
        response = client.post(
            '/api/terminal/start',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'Invalid JSON' in data['error']

    def test_start_transaction_no_terminal_found(self, client):
        """Test transaction start when no terminal is found"""
        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'shopDomain': 'nonexistent.myshopify.com',
                'amount': 1250
            }),
            content_type='application/json'
        )

        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'No matching terminal found' in data['error']

    @responses.activate
    def test_start_transaction_api_error(self, client, terminal):
        """Test transaction start with Pin Vandaag API error"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/start',
            json={'error': 'Terminal offline'},
            status=500
        )

        response = client.post(
            '/api/terminal/start',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'amount': 1250
            }),
            content_type='application/json'
        )

        assert response.status_code == 502
        data = response.json()
        assert data['success'] is False
        assert 'Payment terminal unavailable' in data['error']


@pytest.mark.django_db
class TestGetTransactionStatusView:
    """Test get_transaction_status view"""

    @responses.activate
    def test_get_status_success(self, client, terminal):
        """Test successful status check"""
        # Create transaction in database
        transaction = Transaction.objects.create(
            transaction_id='2405102',
            terminal_link=terminal,
            amount=1250,
            status='started',
            shop_domain='test.myshopify.com'
        )

        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': '2405102',
                'status': 'success',
                'amount': 1250,
                'terminal': '50303253',
                'errorMsg': None,
                'receipt': 'Receipt data...'
            },
            status=200
        )

        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'transaction_id': '2405102'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'success'
        assert data['receipt'] == 'Receipt data...'

        # Verify transaction was updated in database
        transaction.refresh_from_db()
        assert transaction.status == 'success'
        assert transaction.receipt == 'Receipt data...'

    @responses.activate
    def test_get_status_failed_transaction(self, client, terminal):
        """Test status check for failed transaction"""
        transaction = Transaction.objects.create(
            transaction_id='2405103',
            terminal_link=terminal,
            amount=1250,
            status='started',
            shop_domain='test.myshopify.com'
        )

        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': '2405103',
                'status': 'failed',
                'amount': 1250,
                'errorMsg': 'Card declined'
            },
            status=200
        )

        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'transaction_id': '2405103'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'failed'
        assert data['error_msg'] == 'Card declined'

        # Verify transaction was updated
        transaction.refresh_from_db()
        assert transaction.status == 'failed'
        assert transaction.error_msg == 'Card declined'

    @responses.activate
    def test_get_status_still_started(self, client, terminal):
        """Test status check when transaction is still in progress"""
        transaction = Transaction.objects.create(
            transaction_id='2405104',
            terminal_link=terminal,
            amount=1250,
            status='started',
            shop_domain='test.myshopify.com'
        )

        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': '2405104',
                'status': 'started',
                'amount': 1250,
                'terminal': '50303253'
            },
            status=200
        )

        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'transaction_id': '2405104'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'started'

    def test_get_status_missing_shop_domain(self, client):
        """Test status check with missing shopDomain"""
        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'transaction_id': '2405102'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'shopDomain is required' in data['error']

    def test_get_status_missing_transaction_id(self, client, terminal):
        """Test status check with missing transaction_id"""
        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'transaction_id is required' in data['error']

    def test_get_status_no_terminal_found(self, client):
        """Test status check when no terminal is found"""
        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'nonexistent.myshopify.com',
                'transaction_id': '2405102'
            }),
            content_type='application/json'
        )

        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'No matching terminal found' in data['error']

    @responses.activate
    def test_get_status_api_error(self, client, terminal):
        """Test status check with Pin Vandaag API error"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={'error': 'Internal server error'},
            status=500
        )

        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'transaction_id': '2405102'
            }),
            content_type='application/json'
        )

        assert response.status_code == 502
        data = response.json()
        assert data['success'] is False
        assert 'Payment terminal unavailable' in data['error']

    @responses.activate
    def test_get_status_transaction_not_in_db(self, client, terminal):
        """Test status check when transaction doesn't exist in database"""
        # Don't create transaction in database
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': 'unknown-txn',
                'status': 'success',
                'amount': 1250,
                'terminal': '50303253'
            },
            status=200
        )

        response = client.post(
            '/api/terminal/status',
            data=json.dumps({
                'shopDomain': 'test.myshopify.com',
                'transaction_id': 'unknown-txn'
            }),
            content_type='application/json'
        )

        # Should still return success even if transaction not in DB
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'success'
