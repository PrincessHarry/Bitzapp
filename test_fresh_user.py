"""
Test script to demonstrate non-custodial Bitzapp functionality with a fresh user
Shows the complete flow from wallet creation to transactions
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
    handle_create_wallet_command, handle_balance_command, handle_send_command,
    handle_receive_command, handle_wallet_info_command, handle_help_command
)


def create_fresh_user():
    """
    Create a fresh user for testing non-custodial features
    """
    try:
        # Create a new user
        username = 'fresh_user_non_custodial'
        user = User.objects.create_user(
            username=username,
            email=f"{username}@bitzapp.com"
        )
        
        bitzapp_user = BitzappUser.objects.create(
            user=user,
            phone_number='2348123456799',
            is_verified=True
        )
        
        print(f"✅ Created fresh user: {bitzapp_user.phone_number}")
        return bitzapp_user
        
    except Exception as e:
        print(f"❌ Error creating fresh user: {str(e)}")
        return None


def test_complete_non_custodial_flow():
    """
    Test complete non-custodial wallet flow
    """
    print("🔐 Testing Complete Non-Custodial Flow")
    print("=" * 50)
    
    # Create fresh user
    user = create_fresh_user()
    if not user:
        return
    
    try:
        # Test wallet info
        print("\n📋 Step 1: Wallet Information")
        print(handle_wallet_info_command())
        
        # Test help
        print("\n📋 Step 2: Help Command")
        print(handle_help_command())
        
        # Test balance (no wallet yet)
        print("\n💰 Step 3: Check Balance (No Wallet)")
        print(handle_balance_command(user))
        
        # Create non-custodial wallet
        print("\n🔐 Step 4: Create Non-Custodial Wallet")
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
        
        if seed_phrase:
            print(f"\n📝 Extracted seed phrase: {seed_phrase}")
            
            # Test balance after wallet creation
            print("\n💰 Step 5: Check Balance (With Wallet)")
            print(handle_balance_command(user))
            
            # Test receive command
            print("\n📥 Step 6: Get Receive Address")
            print(handle_receive_command(user))
            
            # Test send command (non-custodial)
            print("\n💸 Step 7: Send Bitcoin (Non-Custodial)")
            send_result = handle_send_command(user, f"/send 0.0001 bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh {seed_phrase}")
            print(send_result)
        
        # Test creating wallet again (should show existing)
        print("\n🔐 Step 8: Try Creating Wallet Again")
        print(handle_create_wallet_command(user))
        
        print("\n✅ Complete non-custodial flow test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")


def test_custodial_vs_non_custodial():
    """
    Compare custodial vs non-custodial features
    """
    print("\n🔄 Comparing Custodial vs Non-Custodial")
    print("=" * 40)
    
    try:
        # Get custodial user
        custodial_user = BitzappUser.objects.get(phone_number='2348123456789')
        
        # Get non-custodial user (our fresh user)
        non_custodial_user = BitzappUser.objects.get(phone_number='2348123456799')
        
        print(f"\n🏦 Custodial User: {custodial_user.phone_number}")
        print("Balance Command:")
        print(handle_balance_command(custodial_user))
        
        print(f"\n🔐 Non-Custodial User: {non_custodial_user.phone_number}")
        print("Balance Command:")
        print(handle_balance_command(non_custodial_user))
        
        print("\n✅ Comparison completed!")
        
    except Exception as e:
        print(f"❌ Error during comparison: {str(e)}")


if __name__ == "__main__":
    test_complete_non_custodial_flow()
    test_custodial_vs_non_custodial()
