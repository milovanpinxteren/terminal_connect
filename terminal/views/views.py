import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
import requests

from terminal.models import Transaction
from terminal.services import PinVandaagService, find_terminal

logger = logging.getLogger(__name__)


# =============================================================
# EMBEDDED APP VIEWS (NEW)
# =============================================================
@xframe_options_exempt
@require_GET
def app_home(request):
    """
    Serves the embedded Shopify app home page.
    This is where merchants land after installing the app.
    """
    # Get shop domain from query params (Shopify adds this)
    shop = request.GET.get('shop', '')

    return render(request, 'terminal/app_home.html', {
        'shop': shop,
    })


@require_GET
def get_transactions(request):
    """
    API endpoint to get recent transactions for a shop.

    GET /api/terminal/transactions/?shop=store.myshopify.com
    """
    shop = request.GET.get('shop', '')

    if not shop:
        return JsonResponse({
            'success': False,
            'error': 'shop parameter is required'
        }, status=400)

    # Get last 50 transactions for this shop
    transactions = Transaction.objects.filter(
        shop_domain=shop
    ).order_by('-created_at')[:50]

    data = [{
        'id': tx.id,
        'transaction_id': tx.transaction_id,
        'amount': tx.amount,
        'amount_display': f"€{tx.amount / 100:.2f}",
        'status': tx.status,
        'created_at': tx.created_at.isoformat(),
        'location_id': tx.location_id,
        'staff_member_id': tx.staff_member_id,
    } for tx in transactions]

    return JsonResponse({
        'success': True,
        'transactions': data,
        'count': len(data)
    })


# =============================================================
# POS EXTENSION VIEWS (EXISTING)
# =============================================================

@csrf_exempt
# @require_http_methods(["POST"])
def start_transaction(request):
    """
    Start a new transaction on Pin Vandaag terminal

    POST /api/terminal/start
    Body: {
        "shopDomain": "store.myshopify.com",
        "locationId": "123",
        "staffMemberId": "456",
        "userId": "789",
        "shopId": "012",
        "amount": 1250
    }
    """
    print('starting transaction')
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)

        # Validate required fields
        shop_domain = data.get('shopDomain')
        amount = data.get('amount')

        if not shop_domain:
            return JsonResponse({
                'success': False,
                'error': 'shopDomain is required'
            }, status=400)

        if not amount:
            return JsonResponse({
                'success': False,
                'error': 'amount is required'
            }, status=400)

        # Validate amount is an integer
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'amount must be an integer'
            }, status=400)

        # Extract optional fields
        location_id = data.get('locationId')
        staff_member_id = data.get('staffMemberId')
        user_id = data.get('userId')
        shop_id = data.get('shopId')

        logger.info(f"Starting transaction for shop_domain={shop_domain}, amount={amount}")

        # Find terminal
        terminal = find_terminal(
            shop_domain=shop_domain,
            location_id=location_id,
            staff_member_id=staff_member_id,
            user_id=user_id,
            shop_id=shop_id
        )

        if not terminal:
            logger.warning(f"No matching terminal found for shop_domain={shop_domain}")
            return JsonResponse({
                'success': False,
                'error': 'No matching terminal found'
            }, status=404)

        # Call Pin Vandaag API
        service = PinVandaagService()
        try:
            result = service.start_transaction(
                terminal_id=terminal.terminal_id,
                api_key=terminal.api_key,
                amount=amount
            )
        except requests.RequestException as e:
            logger.error(f"Pin Vandaag API error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Payment terminal unavailable'
            }, status=502)

        # Create Transaction record
        transaction = Transaction.objects.create(
            transaction_id=result.get('transactionId'),
            terminal_link=terminal,
            amount=amount,
            status='started',
            shop_domain=shop_domain,
            location_id=location_id,
            staff_member_id=staff_member_id
        )

        logger.info(f"Transaction created: {transaction.transaction_id}")

        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'status': 'started'
        }, status=200)

    except Exception as e:
        logger.exception(f"Unexpected error in start_transaction: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_transaction_status(request):
    """
    Get status of a transaction

    POST /api/terminal/status
    Body: {
        "shopDomain": "store.myshopify.com",
        "locationId": "123",
        "staffMemberId": "456",
        "userId": "789",
        "shopId": "012",
        "transaction_id": "2405102"
    }
    """
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)

        # Validate required fields
        shop_domain = data.get('shopDomain')
        transaction_id = data.get('transaction_id')

        if not shop_domain:
            return JsonResponse({
                'success': False,
                'error': 'shopDomain is required'
            }, status=400)

        if not transaction_id:
            return JsonResponse({
                'success': False,
                'error': 'transaction_id is required'
            }, status=400)

        # Extract optional fields
        location_id = data.get('locationId')
        staff_member_id = data.get('staffMemberId')
        user_id = data.get('userId')
        shop_id = data.get('shopId')

        logger.info(f"Getting status for transaction_id={transaction_id}")

        # Find terminal
        terminal = find_terminal(
            shop_domain=shop_domain,
            location_id=location_id,
            staff_member_id=staff_member_id,
            user_id=user_id,
            shop_id=shop_id
        )

        if not terminal:
            logger.warning(f"No matching terminal found for shop_domain={shop_domain}")
            return JsonResponse({
                'success': False,
                'error': 'No matching terminal found'
            }, status=404)

        # Call Pin Vandaag API
        service = PinVandaagService()
        try:
            result = service.get_status(
                terminal_id=terminal.terminal_id,
                api_key=terminal.api_key,
                transaction_id=transaction_id
            )
        except requests.RequestException as e:
            logger.error(f"Pin Vandaag API error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Payment terminal unavailable'
            }, status=502)

        # Update Transaction record
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.status = result.get('status', 'started')
            transaction.error_msg = result.get('errorMsg')
            transaction.receipt = result.get('receipt')
            transaction.save()
            logger.info(f"Transaction updated: {transaction_id} -> {transaction.status}")
        except Transaction.DoesNotExist:
            logger.warning(f"Transaction {transaction_id} not found in database")

        return JsonResponse({
            'success': True,
            'status': result.get('status'),
            'error_msg': result.get('errorMsg'),
            'receipt': result.get('receipt')
        }, status=200)

    except Exception as e:
        logger.exception(f"Unexpected error in get_transaction_status: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)