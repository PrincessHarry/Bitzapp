
import json
import logging
import re
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User

from .models import BitzappUser, BitcoinWallet, Transaction
from .command_handlers import (
    handle_create_wallet_command, handle_import_wallet_command, handle_wallet_info_command,
    handle_deposit_command, handle_balance_command, handle_send_command,
    handle_receive_command, handle_paybill_command, handle_withdraw_command,
    handle_ask_command, handle_help_command, handle_unknown_command, handle_ai_chat,
    handle_lightning_invoice_command, handle_lightning_pay_command, 
    handle_lightning_status_command, handle_lightning_history_command
)

logger = logging.getLogger('bitzapp')
VERIFY_TOKEN = "7032318369"


def landing_page(request):
    """
    Landing page for Bitzapp
    """
    return render(request, 'core/landing.html')


def docs_page(request):
    """
    Documentation page for Bitzapp
    """
    return render(request, 'core/docs.html')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    WhatsApp webhook endpoint
    Handles verification and incoming messages
    """
    if request.method == 'GET':
        return handle_webhook_verification(request)
    elif request.method == 'POST':
        return handle_incoming_message(request)


def handle_webhook_verification(request):
    """
    Handle WhatsApp webhook verification
    """
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if verify_token == '7032318369': 
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge)
        else:
            logger.warning("WhatsApp webhook verification failed")
            return HttpResponse('Verification failed', status=403)
            
    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        return HttpResponse('Error', status=500)


def handle_incoming_message(request):
    """
    Handle incoming WhatsApp messages
    """
    try:
        body = json.loads(request.body)
        
        # Process each entry
        for entry in body.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    for message in change.get('value', {}).get('messages', []):
                        process_message(message)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error processing incoming message: {str(e)}")
        return JsonResponse({'status': 'error'}, status=500)


def process_message(message_data):
    """
    Process individual WhatsApp message
    """
    try:
        # Extract message details
        from_number = message_data.get('from')
        message_text = message_data.get('text', {}).get('body', '')
        message_id = message_data.get('id')
        
        logger.info(f"Processing message from {from_number}: {message_text}")
        
        # Get or create user
        user = get_or_create_user(from_number)
        
        # Process command
        response = process_command(user, message_text)
        
        # Send response back to WhatsApp
        send_whatsapp_message(from_number, response)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")


def get_or_create_user(phone_number: str) -> BitzappUser:
    """
    Get or create BitzappUser from phone number
    """
    try:
        # Clean phone number
        phone_number = clean_phone_number(phone_number)
        
        # Try to get existing user
        try:
            bitzapp_user = BitzappUser.objects.get(phone_number=phone_number)
            return bitzapp_user
        except BitzappUser.DoesNotExist:
            pass
        
        # Create new user
        username = f"user_{phone_number}"
        user = User.objects.create_user(
            username=username,
            email=f"{username}@bitzapp.com"
        )
        
        bitzapp_user = BitzappUser.objects.create(
            user=user,
            phone_number=phone_number,
            is_verified=True  # Auto-verify for demo
        )
        
        logger.info(f"Created new user: {phone_number}")
        return bitzapp_user
        
    except Exception as e:
        logger.error(f"Error getting/creating user: {str(e)}")
        raise


def clean_phone_number(phone_number: str) -> str:
    """
    Clean and format phone number
    """
    # Remove non-digits
    phone_number = re.sub(r'\D', '', phone_number)
    
    # Add country code if missing
    if not phone_number.startswith('234'):
        if phone_number.startswith('0'):
            phone_number = '234' + phone_number[1:]
        else:
            phone_number = '234' + phone_number
    
    return phone_number


def process_command(user: BitzappUser, message: str) -> str:
    """
    Process user command and return response
    """
    try:
        message = message.strip().lower()
        
        # Handle different command types
        if message.startswith('/create'):
            return handle_create_wallet_command(user)
        elif message.startswith('/import'):
            return handle_import_wallet_command(user, message)
        elif message.startswith('/wallet'):
            return handle_wallet_info_command()
        elif message.startswith('/save') or message.startswith('/deposit'):
            return handle_deposit_command(user, message)
        elif message.startswith('/balance'):
            return handle_balance_command(user)
        elif message.startswith('/send'):
            return handle_send_command(user, message)
        elif message.startswith('/receive'):
            return handle_receive_command(user)
        elif message.startswith('/paybill'):
            return handle_paybill_command(user, message)
        elif message.startswith('/withdraw'):
            return handle_withdraw_command(user, message)
        elif message.startswith('/lightning '):
            return handle_lightning_invoice_command(user, message)
        elif message.startswith('/lightningpay '):
            return handle_lightning_pay_command(user, message)
        elif message.startswith('/lightningstatus '):
            return handle_lightning_status_command(user, message)
        elif message.startswith('/lightninghistory'):
            return handle_lightning_history_command(user)
        elif message.startswith('/ask'):
            return handle_ask_command(user, message)
        elif message.startswith('/help'):
            return handle_help_command()
        elif message.startswith('/'):
            return handle_unknown_command()
        else:
            # Treat as AI chat
            return handle_ai_chat(user, message)
            
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return "Sorry, I encountered an error processing your request. Please try again."


def send_whatsapp_message(to_number: str, message: str):
    """
    Send WhatsApp message to user using WhatsApp Business Cloud API
    """
    try:
        import requests
        
        whatsapp_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        whatsapp_phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        
        if not whatsapp_token or not whatsapp_phone_number_id:
            logger.warning("WhatsApp API credentials not configured")
            logger.info(f"Demo mode - Would send to {to_number}: {message}")
            return
        
        url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {whatsapp_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"WhatsApp message sent successfully to {to_number}")
        else:
            logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
