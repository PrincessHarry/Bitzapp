"""
Django management command to setup sample data for Bitzapp
Creates sample users, bill providers, and exchange rates
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import BitzappUser, BitcoinWallet, BillProvider, ExchangeRate
from wallet.services import BitcoinWalletService
from decimal import Decimal


class Command(BaseCommand):
    help = 'Setup sample data for Bitzapp'

    def handle(self, *args, **options):
        self.stdout.write('Setting up sample data for Bitzapp...')
        
        # Create sample users
        self.create_sample_users()
        
        # Create bill providers
        self.create_bill_providers()
        
        # Create exchange rates
        self.create_exchange_rates()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup sample data!')
        )

    def create_sample_users(self):
        """Create sample users with Bitcoin wallets"""
        self.stdout.write('Creating sample users...')
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@bitzapp.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        bitzapp_user, created = BitzappUser.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': '2348123456789',
                'is_verified': True
            }
        )
        
        if created:
            # Create custodial Bitcoin wallet for user
            wallet_service = BitcoinWalletService()
            wallet = wallet_service.create_wallet_for_user(bitzapp_user, 'custodial')
            
            # Add some Bitcoin to wallet for testing
            wallet.balance_btc = Decimal('0.001')  # 0.001 BTC
            wallet.save()
            
            self.stdout.write(f'Created custodial user: {bitzapp_user.phone_number}')
        
        # Create another test user
        user2, created = User.objects.get_or_create(
            username='test_user2',
            defaults={
                'email': 'test2@bitzapp.com',
                'first_name': 'Test',
                'last_name': 'User2'
            }
        )
        
        bitzapp_user2, created = BitzappUser.objects.get_or_create(
            user=user2,
            defaults={
                'phone_number': '2348123456790',
                'is_verified': True
            }
        )
        
        if created:
            # Create non-custodial Bitcoin wallet for user
            wallet_service = BitcoinWalletService()
            result = wallet_service.create_wallet_for_user(bitzapp_user2, 'non_custodial')
            wallet = result['wallet']
            wallet.balance_btc = Decimal('0.005')  # 0.005 BTC
            wallet.save()
            
            self.stdout.write(f'Created non-custodial user: {bitzapp_user2.phone_number}')
            self.stdout.write(f'Seed phrase: {result["seed_phrase"]}')

    def create_bill_providers(self):
        """Create sample bill providers"""
        self.stdout.write('Creating bill providers...')
        
        providers = [
            {'name': 'MTN', 'bill_type': 'airtime', 'provider_code': 'MTN_AIRTIME'},
            {'name': 'MTN', 'bill_type': 'data', 'provider_code': 'MTN_DATA'},
            {'name': 'Airtel', 'bill_type': 'airtime', 'provider_code': 'AIRTEL_AIRTIME'},
            {'name': 'Airtel', 'bill_type': 'data', 'provider_code': 'AIRTEL_DATA'},
            {'name': 'PHCN', 'bill_type': 'electricity', 'provider_code': 'PHCN_ELECTRICITY'},
            {'name': 'University of Lagos', 'bill_type': 'school_fees', 'provider_code': 'UNILAG_FEES'},
        ]
        
        for provider_data in providers:
            provider, created = BillProvider.objects.get_or_create(
                name=provider_data['name'],
                bill_type=provider_data['bill_type'],
                defaults={
                    'provider_code': provider_data['provider_code'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created provider: {provider.name} - {provider.bill_type}')

    def create_exchange_rates(self):
        """Create sample exchange rates"""
        self.stdout.write('Creating exchange rates...')
        
        # Create current exchange rate
        ExchangeRate.objects.get_or_create(
            source='bitnob',
            defaults={
                'btc_to_ngn': Decimal('50000000')  # 1 BTC = 50M NGN
            }
        )
        
        self.stdout.write('Created exchange rate: 1 BTC = ₦50,000,000')
