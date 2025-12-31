#!/usr/bin/env python
"""Script to create test terminal configurations"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'terminal_connect.settings')
django.setup()

from terminal.models import TerminalLinks

# Create test terminal configurations
terminals = [
    {
        'shop_domain': 'test.myshopify.com',
        'terminal_id': '50303253',
        'api_key': 'test-api-key-123',
        'location_id': 'loc-123',
        'staff_member_id': None
    },
    {
        'shop_domain': 'demo.myshopify.com',
        'terminal_id': '50303254',
        'api_key': 'demo-api-key-456',
        'location_id': 'loc-456',
        'staff_member_id': 'staff-001'
    },
    {
        'shop_domain': 'test.myshopify.com',
        'terminal_id': '50303255',
        'api_key': 'test-api-key-789',
        'location_id': 'loc-789',
        'staff_member_id': 'staff-002'
    }
]

print("Creating test terminal configurations...")
created_count = 0

for term_data in terminals:
    terminal, created = TerminalLinks.objects.get_or_create(
        shop_domain=term_data['shop_domain'],
        terminal_id=term_data['terminal_id'],
        defaults=term_data
    )

    if created:
        created_count += 1
        print(f"[+] Created: {terminal.shop_domain} -> {terminal.terminal_id}")
    else:
        print(f"[-] Already exists: {terminal.shop_domain} -> {terminal.terminal_id}")

print(f"\nTotal terminals in database: {TerminalLinks.objects.count()}")
print(f"New terminals created: {created_count}")

print("\n--- Terminal Configurations ---")
for terminal in TerminalLinks.objects.all():
    print(f"\nShop: {terminal.shop_domain}")
    print(f"  Terminal ID: {terminal.terminal_id}")
    print(f"  Location ID: {terminal.location_id or 'N/A'}")
    print(f"  Staff Member ID: {terminal.staff_member_id or 'N/A'}")
