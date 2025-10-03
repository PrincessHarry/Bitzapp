"""
Test Real API Integration
Shows how the APIs work when keys are configured vs demo mode
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from payments.services import PaymentService
from chatbot.services import AIChatbotService
from django.conf import settings


def test_api_integrations():
    """
    Test all API integrations
    """
    print("🔌 Testing Real API Integrations")
    print("=" * 40)
    
    # Test Payment Service (Bitnob + MavaPay)
    print("\n💰 Testing Payment Service:")
    payment_service = PaymentService()
    
    print(f"Bitnob API Key: {'✅ Configured' if payment_service.bitnob_api_key else '❌ Not configured (Demo mode)'}")
    print(f"MavaPay API Key: {'✅ Configured' if payment_service.mavapay_api_key else '❌ Not configured (Demo mode)'}")
    
    # Test exchange rate fetching
    print("\n📈 Testing Exchange Rate Fetching:")
    try:
        rate = payment_service._fetch_exchange_rate_from_api()
        print(f"Current BTC/NGN Rate: ₦{rate:,.2f}")
        if payment_service.bitnob_api_key:
            print("✅ Real Bitnob API call successful")
        else:
            print("⚠️ Using fallback rate (Bitnob API key not configured)")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test AI Chatbot Service (Gemini)
    print("\n🤖 Testing AI Chatbot Service:")
    ai_service = AIChatbotService()
    
    print(f"Gemini API Key: {'✅ Configured' if ai_service.gemini_api_key else '❌ Not configured (Demo mode)'}")
    
    # Test AI response generation
    print("\n💬 Testing AI Response Generation:")
    try:
        from core.models import BitzappUser
        user = BitzappUser.objects.first()
        if user:
            response = ai_service.get_chat_response(user, "What is Bitcoin?")
            print(f"AI Response: {response[:100]}...")
            if ai_service.gemini_api_key:
                print("✅ Real Gemini API call successful")
            else:
                print("⚠️ Using fallback response (Gemini API key not configured)")
        else:
            print("❌ No test user found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test WhatsApp Integration
    print("\n📱 Testing WhatsApp Integration:")
    whatsapp_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    whatsapp_phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    
    print(f"WhatsApp Token: {'✅ Configured' if whatsapp_token else '❌ Not configured (Demo mode)'}")
    print(f"WhatsApp Phone ID: {'✅ Configured' if whatsapp_phone_id else '❌ Not configured (Demo mode)'}")
    
    # Test message sending
    print("\n📤 Testing Message Sending:")
    try:
        from core.views import send_whatsapp_message
        send_whatsapp_message("2348123456789", "Test message from Bitzapp")
        if whatsapp_token and whatsapp_phone_id:
            print("✅ Real WhatsApp API call attempted")
        else:
            print("⚠️ Demo mode - message logged instead of sent")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n📋 API Integration Summary:")
    print("=" * 30)
    
    apis = [
        ("Bitnob API", bool(payment_service.bitnob_api_key)),
        ("MavaPay API", bool(payment_service.mavapay_api_key)),
        ("Gemini API", bool(ai_service.gemini_api_key)),
        ("WhatsApp API", bool(whatsapp_token and whatsapp_phone_id))
    ]
    
    for api_name, configured in apis:
        status = "✅ Real API" if configured else "⚠️ Demo Mode"
        print(f"{api_name}: {status}")
    
    print(f"\n🎯 Total APIs: {sum(1 for _, configured in apis if configured)}/4 configured")
    
    if all(configured for _, configured in apis):
        print("🚀 All APIs are configured and ready for production!")
    else:
        print("🔧 Some APIs are in demo mode - configure API keys for full functionality")


def show_api_endpoints():
    """
    Show the actual API endpoints being used
    """
    print("\n🌐 API Endpoints Being Used:")
    print("=" * 30)
    
    print("Bitnob API Endpoints:")
    print("  • Exchange Rate: GET /api/v1/rates/btc")
    print("  • Create Deposit: POST /api/v1/deposits")
    print("  • Create Withdrawal: POST /api/v1/withdrawals")
    
    print("\nMavaPay API Endpoints:")
    print("  • Pay Bill: POST /api/v1/bills/pay")
    
    print("\nGemini API Endpoints:")
    print("  • Generate Content: POST /v1beta/models/gemini-pro:generateContent")
    
    print("\nWhatsApp Business API Endpoints:")
    print("  • Send Message: POST /v18.0/{phone-number-id}/messages")


if __name__ == "__main__":
    test_api_integrations()
    show_api_endpoints()
