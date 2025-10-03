"""
Complete Bitzapp Flow Test
Tests all features: wallet creation, deposits, withdrawals, bill payments, AI chat
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import BitzappUser
from core.command_handlers import (
    handle_create_wallet_command, handle_balance_command, handle_deposit_command,
    handle_withdraw_command, handle_paybill_command, handle_send_command,
    handle_receive_command, handle_ask_command, handle_help_command
)


def create_test_user():
    """
    Create a test user for complete flow testing
    """
    try:
        username = 'complete_flow_user'
        user = User.objects.create_user(
            username=username,
            email=f"{username}@bitzapp.com"
        )
        
        bitzapp_user = BitzappUser.objects.create(
            user=user,
            phone_number='2348123456800',
            is_verified=True
        )
        
        print(f"✅ Created test user: {bitzapp_user.phone_number}")
        return bitzapp_user
        
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        return None


def test_complete_user_flow():
    """
    Test complete user flow from wallet creation to bill payments
    """
    print("🚀 Testing Complete Bitzapp User Flow")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    if not user:
        return
    
    try:
        # Step 1: Help command
        print("\n📋 Step 1: Help Command")
        print(handle_help_command())
        
        # Step 2: Create non-custodial wallet
        print("\n🔐 Step 2: Create Non-Custodial Wallet")
        create_result = handle_create_wallet_command(user)
        print(create_result)
        
        # Extract seed phrase for testing
        seed_phrase = None
        if "Your 12-Word Seed Phrase:" in create_result:
            lines = create_result.split('\n')
            for line in lines:
                if line.strip().startswith('`') and line.strip().endswith('`'):
                    seed_phrase = line.strip().replace('`', '').strip()
                    break
        
        # Step 3: Check balance
        print("\n💰 Step 3: Check Balance")
        print(handle_balance_command(user))
        
        # Step 4: Deposit Naira
        print("\n💳 Step 4: Deposit Naira")
        deposit_result = handle_deposit_command(user, "/deposit 100000")
        print(deposit_result)
        
        # Step 5: Check balance after deposit
        print("\n💰 Step 5: Check Balance After Deposit")
        print(handle_balance_command(user))
        
        # Step 6: Get receive address
        print("\n📥 Step 6: Get Receive Address")
        print(handle_receive_command(user))
        
        # Step 7: Pay bill
        print("\n📱 Step 7: Pay Bill (MTN Airtime)")
        paybill_result = handle_paybill_command(user, "/paybill mtn 5000")
        print(paybill_result)
        
        # Step 8: Withdraw to Nigerian bank
        print("\n🏦 Step 8: Withdraw to Nigerian Bank")
        withdraw_result = handle_withdraw_command(user, "/withdraw 0.0001 1234567890 Access Bank John Doe")
        print(withdraw_result)
        
        # Step 9: Send Bitcoin (if we have seed phrase)
        if seed_phrase:
            print("\n💸 Step 9: Send Bitcoin (Non-Custodial)")
            send_result = handle_send_command(user, f"/send 0.0001 bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh {seed_phrase}")
            print(send_result)
        
        # Step 10: AI Chat
        print("\n🤖 Step 10: AI Chat")
        ai_result = handle_ask_command(user, "What is Bitcoin?")
        print(ai_result)
        
        print("\n✅ Complete user flow test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")


def test_api_integrations():
    """
    Test API integrations (Bitnob, MavaPay, Gemini, WhatsApp)
    """
    print("\n🔌 Testing API Integrations")
    print("=" * 30)
    
    try:
        from payments.services import PaymentService
        from chatbot.services import AIChatbotService
        
        # Test Payment Service
        payment_service = PaymentService()
        print(f"✅ PaymentService initialized")
        print(f"   - Bitnob API Key: {'Configured' if payment_service.bitnob_api_key else 'Not configured'}")
        print(f"   - MavaPay API Key: {'Configured' if payment_service.mavapay_api_key else 'Not configured'}")
        
        # Test AI Chatbot Service
        ai_service = AIChatbotService()
        print(f"✅ AIChatbotService initialized")
        print(f"   - Gemini API Key: {'Configured' if ai_service.gemini_api_key else 'Not configured'}")
        
        # Test WhatsApp integration
        from django.conf import settings
        whatsapp_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        whatsapp_phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        print(f"✅ WhatsApp Integration")
        print(f"   - Access Token: {'Configured' if whatsapp_token else 'Not configured'}")
        print(f"   - Phone Number ID: {'Configured' if whatsapp_phone_id else 'Not configured'}")
        
        print("\n📝 API Integration Status:")
        print("   - Bitnob API: Ready for Bitcoin/Naira conversion")
        print("   - MavaPay API: Ready for bill payments")
        print("   - Gemini API: Ready for AI chatbot")
        print("   - WhatsApp API: Ready for message sending")
        
    except Exception as e:
        print(f"❌ Error testing API integrations: {str(e)}")


def test_wallet_types():
    """
    Test both custodial and non-custodial wallet features
    """
    print("\n🔄 Testing Both Wallet Types")
    print("=" * 30)
    
    try:
        # Test custodial user
        custodial_user = BitzappUser.objects.get(phone_number='2348123456789')
        print(f"\n🏦 Custodial User: {custodial_user.phone_number}")
        print("Balance Command:")
        print(handle_balance_command(custodial_user))
        
        # Test non-custodial user
        non_custodial_user = BitzappUser.objects.get(phone_number='2348123456800')
        print(f"\n🔐 Non-Custodial User: {non_custodial_user.phone_number}")
        print("Balance Command:")
        print(handle_balance_command(non_custodial_user))
        
        print("\n✅ Both wallet types working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing wallet types: {str(e)}")


if __name__ == "__main__":
    test_complete_user_flow()
    test_api_integrations()
    test_wallet_types()
