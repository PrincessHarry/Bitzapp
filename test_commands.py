"""
Test script to demonstrate Bitzapp functionality
Simulates WhatsApp commands and shows responses
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from core.models import BitzappUser
from core.command_handlers import (
    handle_balance_command, handle_deposit_command, handle_send_command,
    handle_receive_command, handle_paybill_command, handle_ask_command,
    handle_help_command
)


def test_bitzapp_commands():
    """
    Test Bitzapp commands with sample user
    """
    print("🚀 Testing Bitzapp Bitcoin Wallet Commands")
    print("=" * 50)
    
    try:
        # Get test user
        user = BitzappUser.objects.get(phone_number='2348123456789')
        print(f"✅ Found test user: {user.phone_number}")
        
        # Test /help command
        print("\n📋 Testing /help command:")
        print(handle_help_command())
        
        # Test /balance command
        print("\n💰 Testing /balance command:")
        print(handle_balance_command(user))
        
        # Test /receive command
        print("\n📥 Testing /receive command:")
        print(handle_receive_command(user))
        
        # Test /deposit command
        print("\n💳 Testing /deposit command:")
        print(handle_deposit_command(user, "/deposit 50000"))
        
        # Test /send command (with insufficient balance)
        print("\n💸 Testing /send command (insufficient balance):")
        print(handle_send_command(user, "/send 0.1 bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"))
        
        # Test /paybill command
        print("\n💳 Testing /paybill command:")
        print(handle_paybill_command(user, "/paybill mtn 1000"))
        
        # Test /ask command
        print("\n🤖 Testing /ask command:")
        print(handle_ask_command(user, "/ask What is Bitcoin?"))
        
        print("\n✅ All tests completed successfully!")
        
    except BitzappUser.DoesNotExist:
        print("❌ Test user not found. Run 'python manage.py setup_sample_data' first.")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")


if __name__ == "__main__":
    test_bitzapp_commands()
