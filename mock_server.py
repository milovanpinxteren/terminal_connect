#!/usr/bin/env python
"""
Mock Pin Vandaag Server for Testing

Simulates Pin Vandaag API V2 endpoints for development and testing.

Usage:
    python mock_server.py --port 8888 --scenario success
    python mock_server.py --port 8888 --scenario fail
    python mock_server.py --port 8888 --scenario instant
    python mock_server.py --port 8888 --scenario timeout
"""

import argparse
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store transaction states in memory
transactions = {}

# Global scenario setting
scenario = 'success'
poll_count = {}


@app.route('/V2/instore/transactions/start', methods=['POST'])
def start_transaction():
    """Start a new transaction"""
    terminal_id = request.form.get('terminal_id')
    amount = request.form.get('amount')
    api_key = request.headers.get('X-API-KEY')

    if not terminal_id or not amount:
        return jsonify({'error': 'Missing required fields'}), 400

    if not api_key:
        return jsonify({'error': 'Missing API key'}), 401

    # Generate a transaction ID
    transaction_id = str(int(time.time() * 1000))

    # Initialize transaction state
    transactions[transaction_id] = {
        'terminal': terminal_id,
        'amount': int(amount),
        'status': 'started',
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scenario': scenario
    }
    poll_count[transaction_id] = 0

    print(f"[START] Transaction {transaction_id} started on terminal {terminal_id}, amount {amount}, scenario: {scenario}")

    return jsonify({
        'transactionId': transaction_id,
        'status': 'started',
        'amount': int(amount),
        'terminal': terminal_id,
        'createdAt': transactions[transaction_id]['createdAt']
    }), 200


@app.route('/V2/instore/transactions/status', methods=['POST'])
def get_status():
    """Get transaction status"""
    terminal_id = request.form.get('terminal_id')
    transaction_id = request.form.get('transaction_id')
    api_key = request.headers.get('X-API-KEY')

    if not terminal_id or not transaction_id:
        return jsonify({'error': 'Missing required fields'}), 400

    if not api_key:
        return jsonify({'error': 'Missing API key'}), 401

    if transaction_id not in transactions:
        return jsonify({'error': 'Transaction not found'}), 404

    txn = transactions[transaction_id]
    poll_count[transaction_id] = poll_count.get(transaction_id, 0) + 1

    current_scenario = txn.get('scenario', scenario)
    polls = poll_count[transaction_id]

    print(f"[STATUS] Transaction {transaction_id} polled (count: {polls}), scenario: {current_scenario}")

    # Handle different scenarios
    if current_scenario == 'instant':
        # Return success immediately
        txn['status'] = 'success'
        txn['receipt'] = generate_receipt(transaction_id, txn['amount'])
        return jsonify({
            'transactionId': transaction_id,
            'status': 'success',
            'amount': txn['amount'],
            'terminal': txn['terminal'],
            'errorMsg': None,
            'receipt': txn['receipt']
        }), 200

    elif current_scenario == 'success':
        # Return success after 3 polls
        if polls >= 3:
            txn['status'] = 'success'
            txn['receipt'] = generate_receipt(transaction_id, txn['amount'])
            return jsonify({
                'transactionId': transaction_id,
                'status': 'success',
                'amount': txn['amount'],
                'terminal': txn['terminal'],
                'errorMsg': None,
                'receipt': txn['receipt']
            }), 200
        else:
            return jsonify({
                'transactionId': transaction_id,
                'status': 'started',
                'amount': txn['amount'],
                'terminal': txn['terminal']
            }), 200

    elif current_scenario == 'fail':
        # Return failure after 2 polls
        if polls >= 2:
            txn['status'] = 'failed'
            txn['errorMsg'] = 'External Equipment Cancellation'
            return jsonify({
                'transactionId': transaction_id,
                'status': 'failed',
                'amount': txn['amount'],
                'terminal': txn['terminal'],
                'errorMsg': txn['errorMsg']
            }), 200
        else:
            return jsonify({
                'transactionId': transaction_id,
                'status': 'started',
                'amount': txn['amount'],
                'terminal': txn['terminal']
            }), 200

    elif current_scenario == 'timeout':
        # Always return started (never completes)
        return jsonify({
            'transactionId': transaction_id,
            'status': 'started',
            'amount': txn['amount'],
            'terminal': txn['terminal']
        }), 200

    else:
        # Default to success after 3 polls
        if polls >= 3:
            txn['status'] = 'success'
            txn['receipt'] = generate_receipt(transaction_id, txn['amount'])
            return jsonify({
                'transactionId': transaction_id,
                'status': 'success',
                'amount': txn['amount'],
                'terminal': txn['terminal'],
                'errorMsg': None,
                'receipt': txn['receipt']
            }), 200
        else:
            return jsonify({
                'transactionId': transaction_id,
                'status': 'started',
                'amount': txn['amount'],
                'terminal': txn['terminal']
            }), 200


def generate_receipt(transaction_id, amount):
    """Generate a mock receipt"""
    return f"""
=====================================
          PIN VANDAAG RECEIPT
=====================================
Transaction ID: {transaction_id}
Amount: €{amount / 100:.2f}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: APPROVED

Thank you for your payment!
=====================================
"""


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'scenario': scenario,
        'transactions': len(transactions)
    }), 200


def main():
    global scenario

    parser = argparse.ArgumentParser(description='Mock Pin Vandaag Server')
    parser.add_argument('--port', type=int, default=8888,
                        help='Port to run server on (default: 8888)')
    parser.add_argument('--scenario', type=str, default='success',
                        choices=['success', 'fail', 'instant', 'timeout'],
                        help='Test scenario to simulate (default: success)')

    args = parser.parse_args()
    scenario = args.scenario

    print(f"""
=====================================
   Mock Pin Vandaag Server
=====================================
Port: {args.port}
Scenario: {args.scenario}

Scenarios:
  success  - Returns started, then success after 3 polls
  fail     - Returns started, then failed after 2 polls
  instant  - Returns success immediately
  timeout  - Never returns success/fail (stays on started)

Endpoints:
  POST /V2/instore/transactions/start
  POST /V2/instore/transactions/status
  GET  /health

Press Ctrl+C to stop
=====================================
    """)

    app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == '__main__':
    main()
