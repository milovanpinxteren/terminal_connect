#!/usr/bin/env python
"""
Comprehensive demo of Terminal Connect functionality
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_start_transaction():
    print_header("TEST 1: Start Transaction")
    response = requests.post(
        f"{BASE_URL}/api/terminal/start",
        json={
            "shopDomain": "test.myshopify.com",
            "amount": 1500
        }
    )
    print_response(response)
    if response.status_code == 200:
        return response.json().get('transaction_id')
    return None

def test_check_status(transaction_id):
    print_header(f"TEST 2: Check Status (Transaction: {transaction_id})")
    for i in range(4):
        print(f"\nPoll {i+1}:")
        response = requests.post(
            f"{BASE_URL}/api/terminal/status",
            json={
                "shopDomain": "test.myshopify.com",
                "transaction_id": transaction_id
            }
        )
        print_response(response)

        data = response.json()
        if data.get('status') == 'success':
            print("\nTransaction completed successfully!")
            break
        elif data.get('status') == 'failed':
            print(f"\nTransaction failed: {data.get('error_msg')}")
            break

        if i < 3:
            print("Waiting 2 seconds before next poll...")
            time.sleep(2)

def test_location_based_routing():
    print_header("TEST 3: Location-Based Terminal Routing")
    print("\nTerminal 50303255 should be selected for location loc-789")
    response = requests.post(
        f"{BASE_URL}/api/terminal/start",
        json={
            "shopDomain": "test.myshopify.com",
            "locationId": "loc-789",
            "amount": 3000
        }
    )
    print_response(response)

def test_error_no_terminal():
    print_header("TEST 4: Error - No Terminal Found")
    response = requests.post(
        f"{BASE_URL}/api/terminal/start",
        json={
            "shopDomain": "nonexistent.myshopify.com",
            "amount": 1000
        }
    )
    print_response(response)

def test_error_missing_field():
    print_header("TEST 5: Error - Missing Required Field")
    response = requests.post(
        f"{BASE_URL}/api/terminal/start",
        json={
            "shopDomain": "test.myshopify.com"
            # amount is missing
        }
    )
    print_response(response)

def test_error_invalid_amount():
    print_header("TEST 6: Error - Invalid Amount")
    response = requests.post(
        f"{BASE_URL}/api/terminal/start",
        json={
            "shopDomain": "test.myshopify.com",
            "amount": "not-a-number"
        }
    )
    print_response(response)

def main():
    print("\n" + "=" * 70)
    print("  Terminal Connect - Comprehensive Demo")
    print("  Testing Shopify POS <-> Pin Vandaag Integration")
    print("=" * 70)

    # Test successful transaction flow
    txn_id = test_start_transaction()
    if txn_id:
        test_check_status(txn_id)

    # Test location-based routing
    test_location_based_routing()

    # Test error scenarios
    test_error_no_terminal()
    test_error_missing_field()
    test_error_invalid_amount()

    print_header("Demo Complete!")
    print("\nAll tests executed. Check the logs above for results.")
    print("\nNext steps:")
    print("  - Visit http://localhost:8000/admin/ to manage terminals")
    print("  - Run 'pytest' to execute the full test suite")
    print("  - Check mock_server.py for different payment scenarios")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to Django server.")
        print("Make sure the server is running: python manage.py runserver")
    except Exception as e:
        print(f"\nError: {e}")
