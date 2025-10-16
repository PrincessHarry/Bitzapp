"""
LNURL Lightning Address Views for Bitzapp
Handles Lightning address resolution and payment requests
"""

import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import BitzappUser
from payments.bitnob_service import BitnobService

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def lnurl_callback(request, username):
    """
    Handle LNURL callback for Lightning address resolution
    GET /.well-known/lnurlp/{username}
    """
    try:
        # Find user by username (phone number without +)
        user = BitzappUser.objects.filter(phone_number__icontains=username).first()
        
        if not user:
            return JsonResponse({
                "status": "ERROR",
                "reason": f"User {username} not found"
            }, status=404)
        
        # Get user's Lightning address info from Bitnob
        bitnob = BitnobService()
        identifier = user.phone_number.replace("+", "").replace("-", "").replace(" ", "")
        
        # Create or get LNURL address
        lnurl_result = bitnob.create_lnurl_address(user.phone_number, identifier)
        
        if not lnurl_result.get("success"):
            return JsonResponse({
                "status": "ERROR",
                "reason": "Failed to get Lightning address"
            }, status=500)
        
        # Return LNURL configuration
        lnurl_config = {
            "status": "OK",
            "tag": "payRequest",
            "commentAllowed": 255,
            "callback": f"https://{settings.ALLOWED_HOSTS[0]}/lnurl/callback/{username}",
            "metadata": json.dumps([
                ["text/plain", f"Payment to {username}@bitzapp-i3i3.onrender.com"],
                ["text/identifier", f"{username}@bitzapp-i3i3.onrender.com"]
            ]),
            "minSendable": lnurl_result.get("sat_min", 1000),
            "maxSendable": lnurl_result.get("sat_max", 1000000),
            "payerData": {
                "name": {"mandatory": False},
                "email": {"mandatory": False}
            }
        }
        
        return JsonResponse(lnurl_config)
        
    except Exception as e:
        logger.error(f"Error in lnurl_callback: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "reason": "Internal server error"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def lnurl_pay_request(request, username):
    """
    Handle LNURL payment request
    GET /lnurl/callback/{username}?amount={msats}&comment={comment}
    """
    try:
        # Get parameters
        amount_msats = request.GET.get('amount')
        comment = request.GET.get('comment', '')
        payer_name = request.GET.get('payerdata', '{}')
        
        if not amount_msats:
            return JsonResponse({
                "status": "ERROR",
                "reason": "Amount parameter required"
            }, status=400)
        
        # Convert millisatoshis to satoshis
        amount_sats = int(amount_msats) // 1000
        
        # Find user
        user = BitzappUser.objects.filter(phone_number__icontains=username).first()
        
        if not user:
            return JsonResponse({
                "status": "ERROR",
                "reason": f"User {username} not found"
            }, status=404)
        
        # Create Lightning invoice via Bitnob
        bitnob = BitnobService()
        invoice_result = bitnob.create_lightning_invoice(
            user.phone_number,
            amount_sats,
            f"Payment to {username}@bitzapp-i3i3.onrender.com"
        )
        
        if not invoice_result.get("success"):
            return JsonResponse({
                "status": "ERROR",
                "reason": "Failed to create invoice"
            }, status=500)
        
        # Return payment request
        payment_request = {
            "status": "OK",
            "pr": invoice_result.get("payment_request"),
            "routes": [],
            "successAction": {
                "tag": "message",
                "message": f"Payment of {amount_sats} sats received!"
            }
        }
        
        return JsonResponse(payment_request)
        
    except Exception as e:
        logger.error(f"Error in lnurl_pay_request: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "reason": "Internal server error"
        }, status=500)


@require_http_methods(["GET"])
def lnurl_withdraw_request(request, username):
    """
    Handle LNURL withdrawal request
    GET /lnurl/withdraw/{username}
    """
    try:
        # Find user
        user = BitzappUser.objects.filter(phone_number__icontains=username).first()
        
        if not user:
            return JsonResponse({
                "status": "ERROR",
                "reason": f"User {username} not found"
            }, status=404)
        
        # Get user's balance
        bitnob = BitnobService()
        balance_result = bitnob.get_wallet_balance(user.phone_number)
        
        if not balance_result.get("success"):
            return JsonResponse({
                "status": "ERROR",
                "reason": "Failed to get balance"
            }, status=500)
        
        balance_sats = balance_result.get("balance_sats", 0)
        
        # Return withdrawal configuration
        withdraw_config = {
            "status": "OK",
            "tag": "withdrawRequest",
            "callback": f"https://{settings.ALLOWED_HOSTS[0]}/lnurl/withdraw/{username}",
            "k1": f"withdraw_{username}_{balance_sats}",
            "defaultDescription": f"Withdraw from {username}@bitzapp-i3i3.onrender.com",
            "minWithdrawable": 1000,  # 1 sat minimum
            "maxWithdrawable": balance_sats * 1000,  # Convert to msats
            "balanceCheck": f"https://{settings.ALLOWED_HOSTS[0]}/lnurl/balance/{username}"
        }
        
        return JsonResponse(withdraw_config)
        
    except Exception as e:
        logger.error(f"Error in lnurl_withdraw_request: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "reason": "Internal server error"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def lnurl_withdraw_callback(request, username):
    """
    Handle LNURL withdrawal callback
    POST /lnurl/withdraw/{username}
    """
    try:
        # Get parameters
        k1 = request.POST.get('k1')
        pr = request.POST.get('pr')  # Lightning invoice
        
        if not k1 or not pr:
            return JsonResponse({
                "status": "ERROR",
                "reason": "Missing required parameters"
            }, status=400)
        
        # Find user
        user = BitzappUser.objects.filter(phone_number__icontains=username).first()
        
        if not user:
            return JsonResponse({
                "status": "ERROR",
                "reason": f"User {username} not found"
            }, status=404)
        
        # Pay the Lightning invoice
        bitnob = BitnobService()
        pay_result = bitnob.pay_lightning_invoice(user.phone_number, pr)
        
        if pay_result.get("success"):
            return JsonResponse({
                "status": "OK"
            })
        else:
            return JsonResponse({
                "status": "ERROR",
                "reason": pay_result.get("error", "Payment failed")
            }, status=400)
        
    except Exception as e:
        logger.error(f"Error in lnurl_withdraw_callback: {str(e)}")
        return JsonResponse({
            "status": "ERROR",
            "reason": "Internal server error"
        }, status=500)
