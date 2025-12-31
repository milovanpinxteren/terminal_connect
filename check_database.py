#!/usr/bin/env python
"""Script to check database contents"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'terminal_connect.settings')
django.setup()

from terminal.models import TerminalLinks, Transaction

print("=" * 60)
print("TERMINAL LINKS")
print("=" * 60)
terminals = TerminalLinks.objects.all()
print(f"Total: {terminals.count()}\n")
for term in terminals:
    print(f"Shop: {term.shop_domain}")
    print(f"  Terminal ID: {term.terminal_id}")
    print(f"  Location: {term.location_id or 'N/A'}")
    print(f"  Staff: {term.staff_member_id or 'N/A'}")
    print()

print("=" * 60)
print("TRANSACTIONS")
print("=" * 60)
transactions = Transaction.objects.all().order_by('-created_at')
print(f"Total: {transactions.count()}\n")
for txn in transactions:
    print(f"Transaction ID: {txn.transaction_id}")
    print(f"  Amount: €{txn.amount / 100:.2f}")
    print(f"  Status: {txn.status}")
    print(f"  Shop: {txn.shop_domain}")
    print(f"  Location: {txn.location_id or 'N/A'}")
    print(f"  Created: {txn.created_at}")
    if txn.error_msg:
        print(f"  Error: {txn.error_msg}")
    if txn.receipt:
        print(f"  Receipt: Yes ({len(txn.receipt)} chars)")
    print()
