# =============================================================
# VOEG TOE AAN JE BESTAANDE views.py
# =============================================================

import hmac
import hashlib
import base64
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_shopify_webhook(request):
    """
    Verifieert de HMAC signature van een Shopify webhook.
    Returns True als geldig, False als ongeldig.
    """
    shopify_hmac = request.headers.get('X-Shopify-Hmac-Sha256', '')

    if not shopify_hmac:
        logger.warning("Webhook ontvangen zonder HMAC header")
        return False

    secret = settings.SHOPIFY_API_SECRET
    if not secret:
        logger.error("SHOPIFY_API_SECRET niet geconfigureerd")
        return False

    # Bereken verwachte HMAC
    computed_hmac = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    # Vergelijk veilig (timing attack safe)
    if hmac.compare_digest(computed_hmac, shopify_hmac):
        return True

    logger.warning("Webhook HMAC verificatie gefaald")
    return False


@csrf_exempt
@require_POST
def shopify_webhook(request):
    """
    Unified webhook endpoint voor alle Shopify GDPR compliance webhooks.
    Leest X-Shopify-Topic header om te bepalen welke webhook het is.

    Topics:
    - customers/data_request: Klant vraagt data op
    - customers/redact: Klant vraagt data verwijdering  
    - shop/redact: Shop verwijdert app

    Wij slaan geen klantdata op, dus we bevestigen alleen ontvangst.
    """
    if not verify_shopify_webhook(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    topic = request.headers.get('X-Shopify-Topic', 'unknown')
    logger.info(f"Shopify webhook ontvangen: {topic}")

    # Geen actie nodig - we slaan geen klantdata op
    # Bij shop/redact zouden we optioneel TerminalLinks kunnen opruimen:
    #
    # if topic == 'shop/redact':
    #     import json
    #     data = json.loads(request.body)
    #     shop_domain = data.get('shop_domain')
    #     TerminalLinks.objects.filter(shop_domain=shop_domain).delete()

    return JsonResponse({})