import pytest
import responses
from requests.exceptions import RequestException
from terminal.services import PinVandaagService, find_terminal
from terminal.models import TerminalLinks


@pytest.mark.django_db
class TestFindTerminal:
    """Test find_terminal service function"""

    def test_find_terminal_by_shop_domain_only(self):
        """Test finding terminal with only shop domain"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='test-api-key'
        )

        found = find_terminal(shop_domain='test.myshopify.com')
        assert found == terminal

    def test_find_terminal_no_match(self):
        """Test finding terminal when no match exists"""
        found = find_terminal(shop_domain='nonexistent.myshopify.com')
        assert found is None

    def test_find_terminal_with_location_filter(self):
        """Test finding terminal filtered by location"""
        # Create multiple terminals for same shop
        terminal1 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='11111',
            api_key='key1',
            location_id='loc-1'
        )
        terminal2 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='22222',
            api_key='key2',
            location_id='loc-2'
        )

        found = find_terminal(
            shop_domain='test.myshopify.com',
            location_id='loc-2'
        )
        assert found == terminal2

    def test_find_terminal_with_staff_member_filter(self):
        """Test finding terminal filtered by staff member"""
        terminal1 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='11111',
            api_key='key1',
            staff_member_id='staff-1'
        )
        terminal2 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='22222',
            api_key='key2',
            staff_member_id='staff-2'
        )

        found = find_terminal(
            shop_domain='test.myshopify.com',
            staff_member_id='staff-1'
        )
        assert found == terminal1

    def test_find_terminal_with_multiple_filters(self):
        """Test finding terminal with multiple filters"""
        terminal = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='12345',
            api_key='key1',
            location_id='loc-1',
            staff_member_id='staff-1',
            user_id='user-1',
            shop_id='shop-1'
        )

        found = find_terminal(
            shop_domain='test.myshopify.com',
            location_id='loc-1',
            staff_member_id='staff-1',
            user_id='user-1',
            shop_id='shop-1'
        )
        assert found == terminal

    def test_find_terminal_filter_priority(self):
        """Test that filters are applied in correct priority order"""
        # Create terminals with different levels of specificity
        terminal1 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='11111',
            api_key='key1'
        )
        terminal2 = TerminalLinks.objects.create(
            shop_domain='test.myshopify.com',
            terminal_id='22222',
            api_key='key2',
            location_id='loc-1'
        )

        # Should return terminal2 when location matches
        found = find_terminal(
            shop_domain='test.myshopify.com',
            location_id='loc-1'
        )
        assert found == terminal2

        # Should return first terminal when location doesn't match
        found = find_terminal(
            shop_domain='test.myshopify.com',
            location_id='loc-999'
        )
        assert found == terminal1


class TestPinVandaagService:
    """Test PinVandaagService"""

    @responses.activate
    def test_start_transaction_success(self):
        """Test successful transaction start"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/start',
            json={
                'transactionId': '2405102',
                'status': 'started',
                'amount': 1000,
                'terminal': '50303253',
                'createdAt': '2022-06-25 17:10:36'
            },
            status=200
        )

        service = PinVandaagService()
        result = service.start_transaction(
            terminal_id='50303253',
            api_key='test-key',
            amount=1000
        )

        assert result['transactionId'] == '2405102'
        assert result['status'] == 'started'
        assert result['amount'] == 1000

        # Verify request was made with correct headers and data
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers['X-API-KEY'] == 'test-key'

    @responses.activate
    def test_start_transaction_api_error(self):
        """Test transaction start with API error"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/start',
            json={'error': 'Invalid terminal'},
            status=400
        )

        service = PinVandaagService()
        with pytest.raises(RequestException):
            service.start_transaction(
                terminal_id='invalid',
                api_key='test-key',
                amount=1000
            )

    @responses.activate
    def test_start_transaction_network_error(self):
        """Test transaction start with network error"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/start',
            body=RequestException('Network error')
        )

        service = PinVandaagService()
        with pytest.raises(RequestException):
            service.start_transaction(
                terminal_id='50303253',
                api_key='test-key',
                amount=1000
            )

    @responses.activate
    def test_get_status_success(self):
        """Test successful status check"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': '2340636',
                'status': 'success',
                'amount': 1000,
                'terminal': '50303253',
                'errorMsg': None,
                'receipt': 'Receipt data...'
            },
            status=200
        )

        service = PinVandaagService()
        result = service.get_status(
            terminal_id='50303253',
            api_key='test-key',
            transaction_id='2340636'
        )

        assert result['transactionId'] == '2340636'
        assert result['status'] == 'success'
        assert result['receipt'] == 'Receipt data...'

    @responses.activate
    def test_get_status_failed_transaction(self):
        """Test status check for failed transaction"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={
                'transactionId': '2340627',
                'status': 'failed',
                'amount': 1000,
                'errorMsg': 'External Equipment Cancellation'
            },
            status=200
        )

        service = PinVandaagService()
        result = service.get_status(
            terminal_id='50303253',
            api_key='test-key',
            transaction_id='2340627'
        )

        assert result['status'] == 'failed'
        assert result['errorMsg'] == 'External Equipment Cancellation'

    @responses.activate
    def test_get_status_api_error(self):
        """Test status check with API error"""
        responses.add(
            responses.POST,
            'https://rest-api.pinvandaag.com/V2/instore/transactions/status',
            json={'error': 'Invalid transaction'},
            status=404
        )

        service = PinVandaagService()
        with pytest.raises(RequestException):
            service.get_status(
                terminal_id='50303253',
                api_key='test-key',
                transaction_id='invalid'
            )

    def test_custom_base_url(self):
        """Test service with custom base URL"""
        custom_url = 'http://localhost:8888/V2'
        service = PinVandaagService(base_url=custom_url)
        assert service.base_url == custom_url
