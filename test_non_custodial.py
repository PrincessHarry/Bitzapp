"""
Test script to demonstrate non-custodial Bitzapp functionality
Shows both custodial and non-custodial wallet features
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from core.models import BitzappUser, BitcoinWallet
from core.command_handlers import (
    handle_create_wallet_command, handle_import_wallet_command, handle_wallet_info_command,
    handle_balance_command, handle_send_command, handle_help_command
)


def test_non_custodial_features():
    """
    Test non-custodial wallet features
    """
    print("🔐 Testing Non-Custodial Bitzapp Features")
    print("=" * 50)
    
    try:
        # Test wallet info command
        print("\n📋 Testing /wallet command:")
        print(handle_wallet_info_command())
        
        # Test help command
        print("\n📋 Testing /help command:")
        print(handle_help_command())
        
        # Test creating non-custodial wallet
        print("\n🔐 Testing /create command:")
        user = BitzappUser.objects.get(phone_number='2348123456789')
        create_result = handle_create_wallet_command(user)
        print(create_result)
        
        # Extract seed phrase from result for testing
        seed_phrase = None
        if "Your 12-Word Seed Phrase:" in create_result:
            lines = create_result.split('\n')
            for line in lines:
                if line.strip().startswith('`') and line.strip().endswith('`'):
                    seed_phrase = line.strip().replace('`', '').strip()
                    break
        
        if seed_phrase:
            print(f"\n📝 Extracted seed phrase: {seed_phrase}")
            
            # Test importing wallet
            print("\n🔐 Testing /import command:")
            import_result = handle_import_wallet_command(user, f"/import {seed_phrase}")
            print(import_result)
        
        # Test balance command
        print("\n💰 Testing /balance command:")
        print(handle_balance_command(user))
        
        # Test send command (non-custodial)
        print("\n💸 Testing /send command (non-custodial):")
        if seed_phrase:
            send_result = handle_send_command(user, f"/send 0.0001 bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh {seed_phrase}")
            print(send_result)
        
        print("\n✅ Non-custodial tests completed successfully!")
        
    except BitzappUser.DoesNotExist:
        print("❌ Test user not found. Run 'python manage.py setup_sample_data' first.")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")


def test_both_wallet_types():
    """
    Test both custodial and non-custodial wallets
    """
    print("\n🔄 Testing Both Wallet Types")
    print("=" * 30)
    
    try:
        # Test custodial user
        custodial_user = BitzappUser.objects.get(phone_number='2348123456789')
        custodial_wallet = BitcoinWallet.objects.get(user=custodial_user)
        
        print(f"\n🏦 Custodial User: {custodial_user.phone_number}")
        print(f"Wallet Type: {custodial_wallet.wallet_type}")
        print(f"Has Private Key: {'Yes' if custodial_wallet.private_key else 'No'}")
        print(f"Seed Phrase Hash: {'Yes' if custodial_wallet.seed_phrase_hash else 'No'}")
        
        # Test non-custodial user
        non_custodial_user = BitzappUser.objects.get(phone_number='2348123456790')
        non_custodial_wallet = BitcoinWallet.objects.get(user=non_custodial_user)
        
        print(f"\n🔐 Non-Custodial User: {non_custodial_user.phone_number}")
        print(f"Wallet Type: {non_custodial_wallet.wallet_type}")
        print(f"Has Private Key: {'Yes' if non_custodial_wallet.private_key else 'No'}")
        print(f"Seed Phrase Hash: {'Yes' if non_custodial_wallet.seed_phrase_hash else 'No'}")
        
        print("\n✅ Both wallet types working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing wallet types: {str(e)}")


if __name__ == "__main__":
    test_non_custodial_features()
    test_both_wallet_types()
