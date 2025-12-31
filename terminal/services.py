import requests
import logging
from django.conf import settings
from .models import TerminalLinks


logger = logging.getLogger(__name__)


class PinVandaagService:
    """Service class for communicating with Pin Vandaag API"""

    def __init__(self, base_url=None):
        self.base_url = base_url or settings.PIN_VANDAAG_BASE_URL

    def start_transaction(self, terminal_id, api_key, amount):
        """
        Start a new transaction on Pin Vandaag terminal

        Args:
            terminal_id: Terminal ID to process payment
            api_key: API key for authentication
            amount: Amount in cents

        Returns:
            dict: Response from Pin Vandaag API

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/instore/transactions/start"
        headers = {
            'X-API-KEY': api_key
        }
        data = {
            'terminal_id': terminal_id,
            'amount': amount
        }

        try:
            logger.debug(f"Starting transaction: terminal={terminal_id}, amount={amount}")
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Transaction started: {result.get('transactionId')}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to start transaction: {e}")
            raise

    def get_status(self, terminal_id, api_key, transaction_id):
        """
        Get status of a transaction

        Args:
            terminal_id: Terminal ID
            api_key: API key for authentication
            transaction_id: Transaction ID to check

        Returns:
            dict: Response from Pin Vandaag API

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/instore/transactions/status"
        headers = {
            'X-API-KEY': api_key
        }
        data = {
            'terminal_id': terminal_id,
            'transaction_id': transaction_id
        }

        try:
            logger.debug(f"Checking status: transaction={transaction_id}")
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Transaction status: {transaction_id} -> {result.get('status')}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to get transaction status: {e}")
            raise


def find_terminal(shop_domain, location_id=None, staff_member_id=None, user_id=None, shop_id=None):
    """
    Find a terminal link based on shop domain and optional filters

    Args:
        shop_domain: Shop domain (required)
        location_id: Location ID (optional)
        staff_member_id: Staff member ID (optional)
        user_id: User ID (optional)
        shop_id: Shop ID (optional)

    Returns:
        TerminalLinks: Matching terminal link or None
    """
    # Start with shop_domain filter (required)
    queryset = TerminalLinks.objects.filter(shop_domain=shop_domain)

    logger.debug(f"Finding terminal for shop_domain={shop_domain}")

    if not queryset.exists():
        logger.warning(f"No terminal found for shop_domain={shop_domain}")
        return None

    # Apply optional filters in order of specificity
    if queryset.count() > 1 and location_id:
        filtered = queryset.filter(location_id=location_id)
        if filtered.exists():
            queryset = filtered
            logger.debug(f"Filtered by location_id={location_id}, found {queryset.count()}")

    if queryset.count() > 1 and staff_member_id:
        filtered = queryset.filter(staff_member_id=staff_member_id)
        if filtered.exists():
            queryset = filtered
            logger.debug(f"Filtered by staff_member_id={staff_member_id}, found {queryset.count()}")

    if queryset.count() > 1 and user_id:
        filtered = queryset.filter(user_id=user_id)
        if filtered.exists():
            queryset = filtered
            logger.debug(f"Filtered by user_id={user_id}, found {queryset.count()}")

    if queryset.count() > 1 and shop_id:
        filtered = queryset.filter(shop_id=shop_id)
        if filtered.exists():
            queryset = filtered
            logger.debug(f"Filtered by shop_id={shop_id}, found {queryset.count()}")

    terminal = queryset.first()
    if terminal:
        logger.info(f"Found terminal: {terminal}")
    else:
        logger.warning("No matching terminal found after filtering")

    return terminal
