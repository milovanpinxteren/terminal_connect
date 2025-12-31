import json
import time

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# In-memory storage for mock transactions
MOCK_TRANSACTIONS = {}


@csrf_exempt
def mock_start_transaction(request):
    """Mock start - returns fake transaction immediately"""
    print('MOCK: Starting transaction')

    transaction_id = f"mock-{int(time.time())}"
    MOCK_TRANSACTIONS[transaction_id] = {
        'started_at': time.time(),
        'amount': 1250,
    }

    return JsonResponse({
        'success': True,
        'transaction_id': transaction_id,
        'status': 'started'
    })


@csrf_exempt
def mock_start_failed(request):
    """Mock start - will fail after 3 seconds"""
    print('MOCK: Starting FAILED transaction')

    transaction_id = f"mock-fail-{int(time.time())}"
    MOCK_TRANSACTIONS[transaction_id] = {
        'started_at': time.time(),
        'will_fail': True,
    }

    return JsonResponse({
        'success': True,
        'transaction_id': transaction_id,
        'status': 'started'
    })


@csrf_exempt
def mock_start_timeout(request):
    """Mock start - will never complete (to test client timeout)"""
    print('MOCK: Starting TIMEOUT transaction')

    transaction_id = f"mock-timeout-{int(time.time())}"
    MOCK_TRANSACTIONS[transaction_id] = {
        'started_at': time.time(),
        'will_timeout': True,
    }

    return JsonResponse({
        'success': True,
        'transaction_id': transaction_id,
        'status': 'started'
    })


@csrf_exempt
def mock_get_transaction_status(request):
    """Mock status - handles success, failed, and timeout scenarios"""
    print('MOCK: Checking status')

    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
    except:
        transaction_id = None

    if not transaction_id or transaction_id not in MOCK_TRANSACTIONS:
        return JsonResponse({
            'success': False,
            'error': 'Transaction not found'
        }, status=404)

    tx = MOCK_TRANSACTIONS[transaction_id]
    elapsed = time.time() - tx['started_at']
    print(f'MOCK: Elapsed time: {elapsed:.1f}s')

    # Timeout scenario - always return 'waiting'
    if tx.get('will_timeout'):
        return JsonResponse({
            'success': True,
            'status': 'waiting'
        })

    # Failed scenario - fail after 3 seconds
    if tx.get('will_fail'):
        if elapsed < 3:
            return JsonResponse({
                'success': True,
                'status': 'waiting'
            })
        else:
            return JsonResponse({
                'success': True,
                'status': 'failed',
                'error_msg': 'Kaart geweigerd'
            })

    # Success scenario - succeed after 5 seconds
    if elapsed < 5:
        return JsonResponse({
            'success': True,
            'status': 'waiting'
        })
    else:
        return JsonResponse({
            'success': True,
            'status': 'success'
        })
