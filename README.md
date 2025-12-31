# Terminal Connect

Django middleware application that connects Shopify POS extensions to Pin Vandaag payment terminals.

## Overview

Terminal Connect acts as a bridge between Shopify POS and Pin Vandaag payment terminals:

1. Shopify POS extension sends payment request to Django
2. Django looks up terminal credentials from database
3. Django initiates payment via Pin Vandaag API
4. POS extension polls Django for transaction status
5. Django returns final payment result

## Features

- RESTful API for payment initiation and status checking
- Flexible terminal lookup based on shop, location, or staff member
- Transaction logging for debugging and reconciliation
- Comprehensive test suite with 36+ tests
- Mock server for development and testing
- Django admin interface for managing terminals and transactions

## Requirements

- Python 3.8+
- Django 4.2+
- See `requirements.txt` for full dependencies

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd terminal_connect
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser for admin access:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Start Transaction

**POST** `/api/terminal/start`

Start a new payment transaction on a Pin Vandaag terminal.

**Request Body:**
```json
{
  "shopDomain": "store.myshopify.com",
  "locationId": "123",
  "staffMemberId": "456",
  "userId": "789",
  "shopId": "012",
  "amount": 1250
}
```

**Required Fields:**
- `shopDomain`: Shopify shop domain
- `amount`: Amount in cents (integer)

**Optional Fields:**
- `locationId`: Shopify location ID
- `staffMemberId`: Staff member ID
- `userId`: User ID
- `shopId`: Shop ID

**Success Response (200):**
```json
{
  "success": true,
  "transaction_id": "2405102",
  "status": "started"
}
```

**Error Responses:**
- `400`: Missing required fields or invalid data
- `404`: No matching terminal found
- `502`: Payment terminal unavailable

### Get Transaction Status

**POST** `/api/terminal/status`

Check the status of a payment transaction.

**Request Body:**
```json
{
  "shopDomain": "store.myshopify.com",
  "locationId": "123",
  "staffMemberId": "456",
  "userId": "789",
  "shopId": "012",
  "transaction_id": "2405102"
}
```

**Required Fields:**
- `shopDomain`: Shopify shop domain
- `transaction_id`: Transaction ID from start request

**Success Response (200):**
```json
{
  "success": true,
  "status": "success",
  "error_msg": null,
  "receipt": "Receipt data..."
}
```

**Status Values:**
- `started`: Payment in progress
- `success`: Payment completed successfully
- `failed`: Payment failed or cancelled

## Terminal Lookup Logic

The system finds the appropriate terminal using the following priority:

1. Match by `shop_domain` (required)
2. If multiple matches, filter by `location_id`
3. If still multiple, filter by `staff_member_id`
4. If still multiple, filter by `user_id`
5. If still multiple, filter by `shop_id`
6. Return first match

This allows for flexible terminal assignment per shop, location, or staff member.

## Database Models

### TerminalLinks

Links Shopify POS sessions to Pin Vandaag terminals.

**Fields:**
- `shop_domain`: Shopify shop domain (indexed)
- `shop_id`: Shop ID (optional)
- `user_id`: User ID (optional)
- `location_id`: Location ID (optional)
- `staff_member_id`: Staff member ID (optional)
- `terminal_id`: Pin Vandaag terminal ID
- `api_key`: Pin Vandaag API key
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Transaction

Logs all payment transactions.

**Fields:**
- `transaction_id`: Pin Vandaag transaction ID (indexed)
- `terminal_link`: Foreign key to TerminalLinks
- `amount`: Amount in cents
- `status`: Transaction status (started/success/failed/timeout)
- `error_msg`: Error message if failed
- `receipt`: Receipt data if successful
- `shop_domain`: Shop domain
- `location_id`: Location ID
- `staff_member_id`: Staff member ID
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Django Admin

Access the admin interface at `/admin/` to manage:

- **Terminal Links**: Configure which terminals are used for each shop/location
- **Transactions**: View transaction history and status

## Testing

Run the test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest terminal/tests/test_views.py
```

The test suite includes:
- Model tests (8 tests)
- Service layer tests (14 tests)
- View/API tests (14 tests)

All tests use mocked HTTP responses for Pin Vandaag API calls.

## Mock Server

For development and testing, use the included mock Pin Vandaag server:

```bash
python mock_server.py --port 8888 --scenario success
```

**Available Scenarios:**

- `success`: Returns started, then success after 3 polls (default)
- `fail`: Returns started, then failed after 2 polls
- `instant`: Returns success immediately
- `timeout`: Never completes (stays on started)

**Update `.env` to use mock server:**
```
PIN_VANDAAG_BASE_URL=http://localhost:8888/V2
```

**Mock Server Endpoints:**
- `POST /V2/instore/transactions/start`
- `POST /V2/instore/transactions/status`
- `GET /health`

## Pin Vandaag API Reference

### Start Transaction

**POST** `https://rest-api.pinvandaag.com/V2/instore/transactions/start`

**Headers:**
- `X-API-KEY`: Your API key

**Form Data:**
- `terminal_id`: Terminal ID
- `amount`: Amount in cents (integer)
- `CallbackUrl`: Callback URL (optional)
- `OwnReference`: Your reference (optional)

**Response:**
```json
{
  "transactionId": "2405102",
  "status": "started",
  "amount": 1,
  "terminal": "50303253",
  "createdAt": "2022-06-25 17:10:36"
}
```

### Get Status

**POST** `https://rest-api.pinvandaag.com/V2/instore/transactions/status`

**Headers:**
- `X-API-KEY`: Your API key

**Form Data:**
- `terminal_id`: Terminal ID
- `transaction_id`: Transaction ID

**Success Response:**
```json
{
  "transactionId": "2340636",
  "status": "success",
  "amount": 1,
  "terminal": "50303253",
  "errorMsg": null,
  "receipt": "..."
}
```

**Failed Response:**
```json
{
  "transactionId": "2340627",
  "status": "failed",
  "amount": 1,
  "errorMsg": "External Equipment Cancellation"
}
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated allowed hosts
- `PIN_VANDAAG_BASE_URL`: Pin Vandaag API base URL

### CORS Settings

By default, CORS is enabled for all origins in development. For production:

1. Update `terminal_connect/settings.py`
2. Change `CORS_ALLOW_ALL_ORIGINS = True` to use specific origins:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-shopify-store.myshopify.com",
]
```

## Production Deployment

### Security Checklist

1. Set `DEBUG = False` in settings
2. Configure `ALLOWED_HOSTS` properly
3. Update `SECRET_KEY` to a secure random value
4. Configure CORS to allow only your Shopify domain
5. Use HTTPS for all communications
6. Use PostgreSQL or MySQL instead of SQLite
7. Set up proper logging and monitoring
8. Enable Django's security middleware
9. Use environment variables for sensitive data
10. Regular database backups

### Database

For production, use PostgreSQL:

```bash
pip install psycopg2-binary
```

Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/terminal_connect
```

Update `settings.py`:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}
```

## Troubleshooting

### No terminal found error

Ensure a TerminalLinks record exists matching the `shop_domain` in your request.

### Payment terminal unavailable

Check that:
1. Pin Vandaag API is accessible
2. API key is valid
3. Terminal ID is correct
4. Network connectivity is working

### Tests failing

1. Ensure all dependencies are installed
2. Check Django settings are correct
3. Run migrations: `python manage.py migrate`

## Development

### Project Structure

```
terminal_connect/
├── terminal_connect/       # Django project settings
│   ├── settings.py
│   └── urls.py
├── terminal/              # Main application
│   ├── models.py         # Database models
│   ├── views.py          # API views
│   ├── services.py       # Business logic
│   ├── admin.py          # Admin configuration
│   ├── urls.py           # URL routing
│   └── tests/            # Test suite
│       ├── test_models.py
│       ├── test_services.py
│       └── test_views.py
├── manage.py             # Django management
├── mock_server.py        # Mock Pin Vandaag server
├── requirements.txt      # Python dependencies
├── pytest.ini           # Pytest configuration
└── conftest.py          # Pytest fixtures
```

### Adding New Features

1. Write tests first (TDD approach)
2. Implement feature
3. Update documentation
4. Run test suite to verify

## License

[Your License Here]

## Support

For issues or questions, please contact [Your Contact Info]
