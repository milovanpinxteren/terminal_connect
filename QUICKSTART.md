# Quick Start Guide

Get Terminal Connect up and running in 5 minutes.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Set Up Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

## 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# For testing with mock server:
# Edit .env and set:
# PIN_VANDAAG_BASE_URL=http://localhost:8888/V2
```

## 4. Add Terminal Configuration

Start Django server:
```bash
python manage.py runserver
```

Visit admin interface: http://localhost:8000/admin/

Add a Terminal Link:
- Shop Domain: `test.myshopify.com`
- Terminal ID: `50303253`
- API Key: `your-api-key`
- Location ID: (optional)
- Staff Member ID: (optional)

## 5. Test with Mock Server (Optional)

In a separate terminal:
```bash
python mock_server.py --port 8888 --scenario success
```

## 6. Make Your First Payment Request

Start a transaction:
```bash
curl -X POST http://localhost:8000/api/terminal/start \
  -H "Content-Type: application/json" \
  -d '{
    "shopDomain": "test.myshopify.com",
    "amount": 1250
  }'
```

Expected response:
```json
{
  "success": true,
  "transaction_id": "2405102",
  "status": "started"
}
```

## 7. Check Transaction Status

```bash
curl -X POST http://localhost:8000/api/terminal/status \
  -H "Content-Type: application/json" \
  -d '{
    "shopDomain": "test.myshopify.com",
    "transaction_id": "2405102"
  }'
```

Expected response (after a few polls):
```json
{
  "success": true,
  "status": "success",
  "error_msg": null,
  "receipt": "..."
}
```

## 8. Run Tests

```bash
pytest
```

All 36 tests should pass!

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Configure production settings for deployment
- Set up real Pin Vandaag API credentials
- Integrate with your Shopify POS extension

## Troubleshooting

**Problem:** "No matching terminal found"
- **Solution:** Add a TerminalLinks record in Django admin matching your shop domain

**Problem:** Mock server not working
- **Solution:** Ensure Flask is installed and port 8888 is available

**Problem:** Tests failing
- **Solution:** Run `python manage.py migrate` first

## Mock Server Scenarios

Test different payment outcomes:

```bash
# Success after 3 polls
python mock_server.py --scenario success

# Immediate failure
python mock_server.py --scenario fail

# Instant success
python mock_server.py --scenario instant

# Never completes (timeout)
python mock_server.py --scenario timeout
```

## Production Setup

See [README.md](README.md) section on "Production Deployment" for security checklist and configuration.
