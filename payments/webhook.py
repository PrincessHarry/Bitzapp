import hmac
import json
import logging
from hashlib import sha256
from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('bitzapp')


def _get_signature_secret() -> bytes:
    secret = getattr(settings, 'BITNOB_WEBHOOK_SECRET', '')
    return secret.encode('utf-8')


def _compute_signature(raw_body: bytes) -> str:
    mac = hmac.new(_get_signature_secret(), msg=raw_body, digestmod=sha256)
    return mac.hexdigest()


def _is_valid_signature(request: HttpRequest, raw_body: bytes) -> bool:
    provided = request.headers.get('X-Bitnob-Signature', '')
    expected = _compute_signature(raw_body)
    try:
        return hmac.compare_digest(provided, expected)
    except Exception:
        return False


def _handle_event(event: str, payload: Dict[str, Any]) -> None:
    # Integrate with application domain here: update orders, credit wallets, etc.
    if event in {
        'checkout.completed',
        'checkout.cancelled',
        'checkout.expired',
        'bank_transfer.received',
        'bank_transfer.reversed',
        'lightning.invoice.paid',
        'wallet.transaction.confirmed',
        'wallet.transaction.failed',
    }:
        logger.info(f"Bitnob webhook handled: {event} | payload keys: {list(payload.keys())}")
    else:
        logger.warning(f"Bitnob webhook unknown event: {event}")


@csrf_exempt
@require_http_methods(["POST"])
def bitnob_webhook(request: HttpRequest) -> HttpResponse:
    raw_body = request.body

    if not _is_valid_signature(request, raw_body):
        logger.warning('Invalid Bitnob webhook signature')
        return JsonResponse({'success': False, 'error': 'invalid signature'}, status=400)

    try:
        data = json.loads(raw_body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'invalid json'}, status=400)

    event = data.get('event') or data.get('type') or ''
    payload = data.get('data') if isinstance(data.get('data'), dict) else data

    _handle_event(event, payload)

    return JsonResponse({'success': True})


