"""
Payment services for Bitzapp
Handles Naira deposits, bill payments, and exchange rate management
"""
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from core.models import BitzappUser, Transaction, ExchangeRate, BillProvider
from payments.models import BillPayment, NairaDeposit, ExchangeRateHistory, NairaWithdrawal, LightningInvoice, LightningPayment

logger = logging.getLogger('bitzapp')


class PaymentService:
    """
    Service for handling Naira deposits and bill payments
    """
    
    def __init__(self):
        self.bitnob_api_key = getattr(settings, 'BITNOB_API_KEY', '')
        self.bitnob_base_url = getattr(settings, 'BITNOB_BASE_URL', 'https://api.bitnob.com')
        self.mavapay_api_key = getattr(settings, 'MAVAPAY_API_KEY', '')
        self.mavapay_base_url = getattr(settings, 'MAVAPAY_BASE_URL', 'https://api.mavapay.co')
    
    def create_naira_deposit(self, user: BitzappUser, amount_ngn: Decimal, payment_method: str = 'bank_transfer') -> NairaDeposit:
        """
        Create a Naira deposit request
        """
        try:
            # Get current exchange rate
            exchange_rate = self._get_current_exchange_rate()
            amount_btc = amount_ngn / exchange_rate
            
            # Create deposit record
            deposit = NairaDeposit.objects.create(
                user=user,
                amount_ngn=amount_ngn,
                amount_btc=amount_btc,
                exchange_rate=exchange_rate,
                payment_method=payment_method,
                status='pending'
            )
            
            logger.info(f"Created Naira deposit: {amount_ngn} NGN for {user.phone_number}")
            return deposit
            
        except Exception as e:
            logger.error(f"Error creating Naira deposit: {str(e)}")
            raise
    
    def process_naira_deposit(self, deposit: NairaDeposit) -> bool:
        """
        Process a Naira deposit and convert to Bitcoin
        """
        try:
            with transaction.atomic():
                # In production, integrate with payment providers
                # For demo, simulate successful payment
                
                # Update deposit status
                deposit.status = 'completed'
                deposit.completed_at = deposit.updated_at
                deposit.save()
                
                # Create Bitcoin transaction
                from wallet.services import BitcoinWalletService
                wallet_service = BitcoinWalletService()
                
                # Add Bitcoin to user's wallet
                from core.models import BitcoinWallet
                user_wallet = BitcoinWallet.objects.get(user=deposit.user)
                user_wallet.balance_btc += deposit.amount_btc
                user_wallet.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=deposit.user,
                    transaction_type='deposit',
                    amount_btc=deposit.amount_btc,
                    amount_ngn=deposit.amount_ngn,
                    description=f"Naira deposit: {deposit.amount_ngn} NGN → {deposit.amount_btc} BTC",
                    exchange_rate=deposit.exchange_rate,
                    status='completed'
                )
                
                logger.info(f"Processed Naira deposit: {deposit.amount_ngn} NGN → {deposit.amount_btc} BTC")
                return True
                
        except Exception as e:
            logger.error(f"Error processing Naira deposit: {str(e)}")
            deposit.status = 'failed'
            deposit.save()
            return False
    
    def pay_bill(self, user: BitzappUser, provider: BillProvider, customer_reference: str, 
                 amount_ngn: Decimal, bill_reference: str = "") -> BillPayment:
        """
        Pay a bill using Bitcoin
        """
        try:
            with transaction.atomic():
                # Get current exchange rate
                exchange_rate = self._get_current_exchange_rate()
                amount_btc = amount_ngn / exchange_rate
                
                # Check user's Bitcoin balance
                from core.models import BitcoinWallet
                user_wallet = BitcoinWallet.objects.get(user=user)
                
                if user_wallet.balance_btc < amount_btc:
                    raise ValueError("Insufficient Bitcoin balance")
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    user=user,
                    transaction_type='bill_payment',
                    amount_btc=amount_btc,
                    amount_ngn=amount_ngn,
                    bill_type=provider.bill_type,
                    bill_reference=bill_reference,
                    description=f"Bill payment: {provider.name} - {amount_ngn} NGN",
                    exchange_rate=exchange_rate,
                    status='pending'
                )
                
                # Create bill payment record
                bill_payment = BillPayment.objects.create(
                    transaction=transaction_obj,
                    provider=provider,
                    customer_reference=customer_reference,
                    bill_reference=bill_reference,
                    amount_ngn=amount_ngn,
                    amount_btc=amount_btc,
                    status='pending'
                )
                
                # Process the bill payment
                success = self._process_bill_payment(bill_payment)
                
                if success:
                    # Update user's Bitcoin balance
                    user_wallet.balance_btc -= amount_btc
                    user_wallet.save()
                    
                    # Update transaction status
                    transaction_obj.status = 'completed'
                    transaction_obj.completed_at = transaction_obj.updated_at
                    transaction_obj.save()
                    
                    bill_payment.status = 'completed'
                    bill_payment.processed_at = bill_payment.updated_at
                    bill_payment.save()
                
                logger.info(f"Bill payment processed: {amount_ngn} NGN for {user.phone_number}")
                return bill_payment
                
        except Exception as e:
            logger.error(f"Error paying bill: {str(e)}")
            raise
    
    def _process_bill_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process bill payment with external provider using MavaPay API
        """
        try:
            if not self.mavapay_api_key:
                logger.warning("MavaPay API key not configured, using demo mode")
                return self._process_demo_payment(bill_payment)
            
            # Use MavaPay API for all bill payments
            return self._process_mavapay_payment(bill_payment)
                
        except Exception as e:
            logger.error(f"Error processing bill payment: {str(e)}")
            return False
    
    def _process_mavapay_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process bill payment using MavaPay API
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.mavapay_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare payment data for MavaPay
            data = {
                'amount': float(bill_payment.amount_ngn),
                'currency': 'NGN',
                'provider': bill_payment.provider.provider_code,
                'customer_reference': bill_payment.customer_reference,
                'bill_reference': bill_payment.bill_reference,
                'description': f'Bill payment via Bitzapp - {bill_payment.provider.name}'
            }
            
            response = requests.post(
                f"{self.mavapay_base_url}/api/v1/bills/pay",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update bill payment with MavaPay response
                bill_payment.provider_transaction_id = result.get('transaction_id')
                bill_payment.provider_response = result.get('status')
                bill_payment.provider_reference = result.get('reference')
                bill_payment.save()
                
                logger.info(f"MavaPay payment processed: {bill_payment.customer_reference}")
                return True
            else:
                logger.error(f"MavaPay API error: {response.status_code} - {response.text}")
                bill_payment.provider_response = f"Error: {response.status_code}"
                bill_payment.save()
                return False
                
        except Exception as e:
            logger.error(f"Error processing MavaPay payment: {str(e)}")
            return False
    
    def _process_demo_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process demo payment when APIs are not configured
        """
        try:
            bill_payment.provider_transaction_id = f"DEMO_{bill_payment.id}"
            bill_payment.provider_response = "Demo payment successful"
            bill_payment.save()
            
            logger.info(f"Demo payment processed: {bill_payment.customer_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing demo payment: {str(e)}")
            return False
    
    def _process_mtn_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process MTN airtime/data payment
        """
        try:
            # In production, integrate with MTN API
            # For demo, simulate successful payment
            bill_payment.provider_transaction_id = f"MTN_{bill_payment.id}"
            bill_payment.provider_response = "Payment successful"
            bill_payment.save()
            
            logger.info(f"MTN payment processed: {bill_payment.customer_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing MTN payment: {str(e)}")
            return False
    
    def _process_airtel_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process Airtel airtime/data payment
        """
        try:
            # In production, integrate with Airtel API
            # For demo, simulate successful payment
            bill_payment.provider_transaction_id = f"AIRTEL_{bill_payment.id}"
            bill_payment.provider_response = "Payment successful"
            bill_payment.save()
            
            logger.info(f"Airtel payment processed: {bill_payment.customer_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Airtel payment: {str(e)}")
            return False
    
    def _process_electricity_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process electricity bill payment
        """
        try:
            # In production, integrate with electricity provider API
            # For demo, simulate successful payment
            bill_payment.provider_transaction_id = f"ELECTRICITY_{bill_payment.id}"
            bill_payment.provider_response = "Payment successful"
            bill_payment.save()
            
            logger.info(f"Electricity payment processed: {bill_payment.customer_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing electricity payment: {str(e)}")
            return False
    
    def _process_generic_payment(self, bill_payment: BillPayment) -> bool:
        """
        Process generic bill payment
        """
        try:
            # In production, integrate with generic payment API
            # For demo, simulate successful payment
            bill_payment.provider_transaction_id = f"GENERIC_{bill_payment.id}"
            bill_payment.provider_response = "Payment successful"
            bill_payment.save()
            
            logger.info(f"Generic payment processed: {bill_payment.customer_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing generic payment: {str(e)}")
            return False
    
    def _get_current_exchange_rate(self) -> Decimal:
        """
        Get current BTC to NGN exchange rate
        """
        try:
            # Try to get from database first
            latest_rate = ExchangeRate.objects.filter(
                source='bitnob'
            ).order_by('-created_at').first()
            
            if latest_rate:
                return latest_rate.btc_to_ngn
            
            # If no rate in database, fetch from API
            return self._fetch_exchange_rate_from_api()
            
        except Exception as e:
            logger.error(f"Error getting exchange rate: {str(e)}")
            # Return fallback rate
            return Decimal('50000000')  # 1 BTC = 50M NGN (placeholder)
    
    def _fetch_exchange_rate_from_api(self) -> Decimal:
        """
        Fetch exchange rate from Bitnob API
        """
        try:
            if not self.bitnob_api_key:
                logger.warning("Bitnob API key not configured")
                return Decimal('50000000')
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Fetch BTC price in NGN from Bitnob API
            response = requests.get(
                f"{self.bitnob_base_url}/api/v1/rates/btc",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Bitnob API returns rate in NGN per BTC
                rate = Decimal(str(data.get('rate', 50000000)))
                
                # Save to database
                ExchangeRate.objects.create(
                    btc_to_ngn=rate,
                    source='bitnob'
                )
                
                # Save to history
                ExchangeRateHistory.objects.create(
                    btc_to_ngn=rate,
                    source='bitnob'
                )
                
                logger.info(f"Fetched exchange rate from Bitnob: 1 BTC = ₦{rate:,.2f}")
                return rate
            else:
                logger.error(f"Bitnob API error: {response.status_code} - {response.text}")
                return Decimal('50000000')
                
        except Exception as e:
            logger.error(f"Error fetching exchange rate from API: {str(e)}")
            return Decimal('50000000')
    
    def create_naira_deposit_with_bitnob(self, user: BitzappUser, amount_ngn: Decimal) -> dict:
        """
        Create Naira deposit using Bitnob API
        """
        try:
            if not self.bitnob_api_key:
                raise ValueError("Bitnob API key not configured")
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Create deposit request with Bitnob
            data = {
                'amount': float(amount_ngn),
                'currency': 'NGN',
                'description': f'Naira deposit for {user.phone_number}',
                'customer_reference': user.phone_number
            }
            
            response = requests.post(
                f"{self.bitnob_base_url}/api/v1/deposits",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Create local deposit record
                exchange_rate = self._get_current_exchange_rate()
                amount_btc = amount_ngn / exchange_rate
                
                deposit = NairaDeposit.objects.create(
                    user=user,
                    amount_ngn=amount_ngn,
                    amount_btc=amount_btc,
                    exchange_rate=exchange_rate,
                    payment_method='bitnob',
                    status='pending',
                    provider_transaction_id=result.get('id'),
                    provider_response=result.get('status')
                )
                
                logger.info(f"Created Bitnob deposit: {amount_ngn} NGN for {user.phone_number}")
                return {
                    'deposit': deposit,
                    'bitnob_response': result,
                    'payment_url': result.get('payment_url'),
                    'status': 'pending'
                }
            else:
                logger.error(f"Bitnob deposit error: {response.status_code} - {response.text}")
                raise ValueError("Failed to create deposit with Bitnob")
                
        except Exception as e:
            logger.error(f"Error creating Bitnob deposit: {str(e)}")
            raise
    
    def get_bill_providers(self, bill_type: str = None) -> list:
        """
        Get available bill payment providers
        """
        try:
            providers = BillProvider.objects.filter(is_active=True)
            
            if bill_type:
                providers = providers.filter(bill_type=bill_type)
            
            return [
                {
                    'id': provider.id,
                    'name': provider.name,
                    'bill_type': provider.bill_type,
                    'provider_code': provider.provider_code
                }
                for provider in providers
            ]
            
        except Exception as e:
            logger.error(f"Error getting bill providers: {str(e)}")
            return []
    
    def get_payment_history(self, user: BitzappUser, limit: int = 10) -> list:
        """
        Get user's payment history
        """
        try:
            # Get bill payments
            bill_payments = BillPayment.objects.filter(
                transaction__user=user
            ).order_by('-created_at')[:limit]
            
            # Get Naira deposits
            naira_deposits = NairaDeposit.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            history = []
            
            # Add bill payments to history
            for payment in bill_payments:
                history.append({
                    'type': 'bill_payment',
                    'provider': payment.provider.name,
                    'amount_ngn': float(payment.amount_ngn),
                    'amount_btc': float(payment.amount_btc),
                    'status': payment.status,
                    'created_at': payment.created_at.isoformat()
                })
            
            # Add Naira deposits to history
            for deposit in naira_deposits:
                history.append({
                    'type': 'naira_deposit',
                    'amount_ngn': float(deposit.amount_ngn),
                    'amount_btc': float(deposit.amount_btc),
                    'status': deposit.status,
                    'created_at': deposit.created_at.isoformat()
                })
            
            # Sort by creation date
            history.sort(key=lambda x: x['created_at'], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting payment history for {user.phone_number}: {str(e)}")
            return []
    
    def create_naira_withdrawal(self, user: BitzappUser, amount_btc: Decimal, 
                               bank_account_number: str, bank_name: str, account_name: str) -> NairaWithdrawal:
        """
        Create a Naira withdrawal request (Bitcoin to Nigerian bank account)
        """
        try:
            with transaction.atomic():
                # Get current exchange rate
                exchange_rate = self._get_current_exchange_rate()
                amount_ngn = amount_btc * exchange_rate
                
                # Check user's Bitcoin balance
                from core.models import BitcoinWallet
                user_wallet = BitcoinWallet.objects.get(user=user)
                
                if user_wallet.balance_btc < amount_btc:
                    raise ValueError("Insufficient Bitcoin balance")
                
                # Create withdrawal record
                withdrawal = NairaWithdrawal.objects.create(
                    user=user,
                    amount_btc=amount_btc,
                    amount_ngn=amount_ngn,
                    exchange_rate=exchange_rate,
                    bank_account_number=bank_account_number,
                    bank_name=bank_name,
                    account_name=account_name,
                    status='pending'
                )
                
                logger.info(f"Created Naira withdrawal: {amount_btc} BTC → ₦{amount_ngn} for {user.phone_number}")
                return withdrawal
                
        except Exception as e:
            logger.error(f"Error creating Naira withdrawal: {str(e)}")
            raise
    
    def process_naira_withdrawal(self, withdrawal: NairaWithdrawal) -> bool:
        """
        Process Naira withdrawal using Bitnob API
        """
        try:
            with transaction.atomic():
                # Update status to processing
                withdrawal.status = 'processing'
                withdrawal.save()
                
                # Process with Bitnob API
                success = self._process_withdrawal_with_bitnob(withdrawal)
                
                if success:
                    # Update user's Bitcoin balance
                    from core.models import BitcoinWallet
                    user_wallet = BitcoinWallet.objects.get(user=withdrawal.user)
                    user_wallet.balance_btc -= withdrawal.amount_btc
                    user_wallet.save()
                    
                    # Create transaction record
                    Transaction.objects.create(
                        user=withdrawal.user,
                        transaction_type='withdrawal',
                        amount_btc=withdrawal.amount_btc,
                        amount_ngn=withdrawal.amount_ngn,
                        description=f"Naira withdrawal: {withdrawal.amount_btc} BTC → ₦{withdrawal.amount_ngn} to {withdrawal.bank_name}",
                        exchange_rate=withdrawal.exchange_rate,
                        status='completed'
                    )
                    
                    # Update withdrawal status
                    withdrawal.status = 'completed'
                    withdrawal.completed_at = withdrawal.updated_at
                    withdrawal.save()
                    
                    logger.info(f"Processed Naira withdrawal: {withdrawal.amount_btc} BTC → ₦{withdrawal.amount_ngn}")
                    return True
                else:
                    withdrawal.status = 'failed'
                    withdrawal.save()
                    return False
                    
        except Exception as e:
            logger.error(f"Error processing Naira withdrawal: {str(e)}")
            withdrawal.status = 'failed'
            withdrawal.save()
            return False
    
    def _process_withdrawal_with_bitnob(self, withdrawal: NairaWithdrawal) -> bool:
        """
        Process withdrawal using Bitnob API
        """
        try:
            if not self.bitnob_api_key:
                logger.warning("Bitnob API key not configured, using demo mode")
                return self._process_demo_withdrawal(withdrawal)
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare withdrawal data for Bitnob
            data = {
                'amount': float(withdrawal.amount_ngn),
                'currency': 'NGN',
                'bank_account_number': withdrawal.bank_account_number,
                'bank_name': withdrawal.bank_name,
                'account_name': withdrawal.account_name,
                'description': f'Naira withdrawal for {withdrawal.user.phone_number}',
                'customer_reference': withdrawal.user.phone_number
            }
            
            response = requests.post(
                f"{self.bitnob_base_url}/api/v1/withdrawals",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update withdrawal with Bitnob response
                withdrawal.provider_transaction_id = result.get('transaction_id')
                withdrawal.provider_response = result.get('status')
                withdrawal.save()
                
                logger.info(f"Bitnob withdrawal processed: {withdrawal.bank_account_number}")
                return True
            else:
                logger.error(f"Bitnob withdrawal error: {response.status_code} - {response.text}")
                withdrawal.provider_response = f"Error: {response.status_code}"
                withdrawal.save()
                return False
                
        except Exception as e:
            logger.error(f"Error processing Bitnob withdrawal: {str(e)}")
            return False
    
    def _process_demo_withdrawal(self, withdrawal: NairaWithdrawal) -> bool:
        """
        Process demo withdrawal when APIs are not configured
        """
        try:
            withdrawal.provider_transaction_id = f"DEMO_WITHDRAWAL_{withdrawal.id}"
            withdrawal.provider_response = "Demo withdrawal successful"
            withdrawal.save()
            
            logger.info(f"Demo withdrawal processed: {withdrawal.bank_account_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing demo withdrawal: {str(e)}")
            return False
    
    # Lightning Network Methods
    
    def create_lightning_invoice(self, user: BitzappUser, amount_sats: int, description: str = "", memo: str = "") -> LightningInvoice:
        """
        Create a Lightning Network invoice using Bitnob API
        """
        try:
            from datetime import datetime, timedelta
            
            # Convert satoshis to BTC and NGN
            amount_btc = Decimal(amount_sats) / Decimal('100000000')  # 1 BTC = 100M sats
            exchange_rate = self._get_current_exchange_rate()
            amount_ngn = amount_btc * exchange_rate
            
            # Create Lightning invoice using Bitnob API
            if not self.bitnob_api_key:
                logger.warning("Bitnob API key not configured, using demo mode")
                return self._create_demo_lightning_invoice(user, amount_sats, amount_btc, amount_ngn, description, memo)
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare invoice data for Bitnob Lightning API
            data = {
                'amount': amount_sats,
                'currency': 'sats',
                'description': description or f'Lightning invoice for {user.phone_number}',
                'memo': memo or f'Bitzapp Lightning Payment',
                'expiry': 3600,  # 1 hour expiry
                'customer_reference': user.phone_number
            }
            
            response = requests.post(
                f"{self.bitnob_base_url}/api/v1/lightning/invoices",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Create Lightning invoice record
                invoice = LightningInvoice.objects.create(
                    user=user,
                    payment_request=result.get('payment_request'),
                    payment_hash=result.get('payment_hash'),
                    amount_sats=amount_sats,
                    amount_btc=amount_btc,
                    amount_ngn=amount_ngn,
                    description=description,
                    memo=memo,
                    expires_at=datetime.now() + timedelta(hours=1),
                    provider_transaction_id=result.get('id'),
                    provider_response=result.get('status')
                )
                
                logger.info(f"Created Lightning invoice: {amount_sats} sats for {user.phone_number}")
                return invoice
            else:
                logger.error(f"Bitnob Lightning invoice error: {response.status_code} - {response.text}")
                raise ValueError("Failed to create Lightning invoice with Bitnob")
                
        except Exception as e:
            logger.error(f"Error creating Lightning invoice: {str(e)}")
            raise
    
    def _create_demo_lightning_invoice(self, user: BitzappUser, amount_sats: int, amount_btc: Decimal, 
                                     amount_ngn: Decimal, description: str, memo: str) -> LightningInvoice:
        """
        Create demo Lightning invoice when APIs are not configured
        """
        try:
            from datetime import datetime, timedelta
            
            # Generate demo payment request (fake BOLT11 format)
            demo_payment_request = f"lnbc{amount_sats}u1p{amount_sats}sp1..."  # Simplified demo format
            
            invoice = LightningInvoice.objects.create(
                user=user,
                payment_request=demo_payment_request,
                payment_hash=f"demo_hash_{amount_sats}_{user.id}",
                amount_sats=amount_sats,
                amount_btc=amount_btc,
                amount_ngn=amount_ngn,
                description=description,
                memo=memo,
                expires_at=datetime.now() + timedelta(hours=1),
                provider_transaction_id=f"DEMO_LIGHTNING_{amount_sats}",
                provider_response="Demo Lightning invoice created"
            )
            
            logger.info(f"Created demo Lightning invoice: {amount_sats} sats for {user.phone_number}")
            return invoice
            
        except Exception as e:
            logger.error(f"Error creating demo Lightning invoice: {str(e)}")
            raise
    
    def pay_lightning_invoice(self, user: BitzappUser, payment_request: str, description: str = "", memo: str = "") -> LightningPayment:
        """
        Pay a Lightning Network invoice using Bitnob API
        """
        try:
            # Parse payment request to get amount (simplified for demo)
            # In production, use proper BOLT11 parsing library
            amount_sats = self._parse_payment_request_amount(payment_request)
            amount_btc = Decimal(amount_sats) / Decimal('100000000')
            exchange_rate = self._get_current_exchange_rate()
            amount_ngn = amount_btc * exchange_rate
            
            # Check user's Bitcoin balance
            from core.models import BitcoinWallet
            user_wallet = BitcoinWallet.objects.get(user=user)
            
            if user_wallet.balance_btc < amount_btc:
                raise ValueError("Insufficient Bitcoin balance")
            
            # Create Lightning payment using Bitnob API
            if not self.bitnob_api_key:
                logger.warning("Bitnob API key not configured, using demo mode")
                return self._create_demo_lightning_payment(user, payment_request, amount_sats, amount_btc, amount_ngn, description, memo)
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare payment data for Bitnob Lightning API
            data = {
                'payment_request': payment_request,
                'description': description or f'Lightning payment from {user.phone_number}',
                'memo': memo or 'Bitzapp Lightning Payment',
                'customer_reference': user.phone_number
            }
            
            response = requests.post(
                f"{self.bitnob_base_url}/api/v1/lightning/payments",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Create Lightning payment record
                payment = LightningPayment.objects.create(
                    user=user,
                    payment_request=payment_request,
                    payment_hash=result.get('payment_hash'),
                    amount_sats=amount_sats,
                    amount_btc=amount_btc,
                    amount_ngn=amount_ngn,
                    description=description,
                    memo=memo,
                    provider_transaction_id=result.get('id'),
                    provider_response=result.get('status')
                )
                
                # Update user's Bitcoin balance
                user_wallet.balance_btc -= amount_btc
                user_wallet.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=user,
                    transaction_type='lightning_payment',
                    amount_btc=amount_btc,
                    amount_ngn=amount_ngn,
                    description=f"Lightning payment: {amount_sats} sats",
                    exchange_rate=exchange_rate,
                    status='completed'
                )
                
                # Update payment status
                payment.status = 'completed'
                payment.completed_at = payment.updated_at
                payment.save()
                
                logger.info(f"Processed Lightning payment: {amount_sats} sats for {user.phone_number}")
                return payment
            else:
                logger.error(f"Bitnob Lightning payment error: {response.status_code} - {response.text}")
                raise ValueError("Failed to process Lightning payment with Bitnob")
                
        except Exception as e:
            logger.error(f"Error processing Lightning payment: {str(e)}")
            raise
    
    def _create_demo_lightning_payment(self, user: BitzappUser, payment_request: str, amount_sats: int, 
                                     amount_btc: Decimal, amount_ngn: Decimal, description: str, memo: str) -> LightningPayment:
        """
        Create demo Lightning payment when APIs are not configured
        """
        try:
            # Check user's Bitcoin balance
            from core.models import BitcoinWallet
            user_wallet = BitcoinWallet.objects.get(user=user)
            
            if user_wallet.balance_btc < amount_btc:
                raise ValueError("Insufficient Bitcoin balance")
            
            # Create Lightning payment record
            payment = LightningPayment.objects.create(
                user=user,
                payment_request=payment_request,
                payment_hash=f"demo_payment_hash_{amount_sats}_{user.id}",
                amount_sats=amount_sats,
                amount_btc=amount_btc,
                amount_ngn=amount_ngn,
                description=description,
                memo=memo,
                provider_transaction_id=f"DEMO_LIGHTNING_PAYMENT_{amount_sats}",
                provider_response="Demo Lightning payment processed"
            )
            
            # Update user's Bitcoin balance
            user_wallet.balance_btc -= amount_btc
            user_wallet.save()
            
            # Create transaction record
            exchange_rate = self._get_current_exchange_rate()
            Transaction.objects.create(
                user=user,
                transaction_type='lightning_payment',
                amount_btc=amount_btc,
                amount_ngn=amount_ngn,
                description=f"Lightning payment: {amount_sats} sats",
                exchange_rate=exchange_rate,
                status='completed'
            )
            
            # Update payment status
            payment.status = 'completed'
            payment.completed_at = payment.updated_at
            payment.save()
            
            logger.info(f"Processed demo Lightning payment: {amount_sats} sats for {user.phone_number}")
            return payment
            
        except Exception as e:
            logger.error(f"Error creating demo Lightning payment: {str(e)}")
            raise
    
    def _parse_payment_request_amount(self, payment_request: str) -> int:
        """
        Parse Lightning payment request to extract amount in satoshis
        Simplified implementation for demo purposes
        """
        try:
            # This is a simplified parser for demo purposes
            # In production, use proper BOLT11 parsing library like pyln-client
            
            # Extract amount from payment request (simplified regex)
            import re
            
            # Look for amount pattern in BOLT11 format
            amount_match = re.search(r'lnbc(\d+)', payment_request)
            if amount_match:
                return int(amount_match.group(1))
            
            # Fallback: return a default amount for demo
            return 1000  # 1000 sats default
            
        except Exception as e:
            logger.error(f"Error parsing payment request amount: {str(e)}")
            return 1000  # Default fallback
    
    def get_lightning_invoice_status(self, invoice: LightningInvoice) -> dict:
        """
        Check Lightning invoice status using Bitnob API
        """
        try:
            if not self.bitnob_api_key:
                logger.warning("Bitnob API key not configured, returning demo status")
                return {
                    'status': 'paid' if invoice.status == 'paid' else 'pending',
                    'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
                    'amount_sats': invoice.amount_sats
                }
            
            headers = {
                'Authorization': f'Bearer {self.bitnob_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.bitnob_base_url}/api/v1/lightning/invoices/{invoice.provider_transaction_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update invoice status if changed
                if result.get('status') == 'paid' and invoice.status != 'paid':
                    invoice.status = 'paid'
                    from datetime import datetime
                    invoice.paid_at = datetime.now()
                    invoice.save()
                
                return {
                    'status': result.get('status'),
                    'paid_at': result.get('paid_at'),
                    'amount_sats': invoice.amount_sats
                }
            else:
                logger.error(f"Bitnob Lightning invoice status error: {response.status_code} - {response.text}")
                return {
                    'status': invoice.status,
                    'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
                    'amount_sats': invoice.amount_sats
                }
                
        except Exception as e:
            logger.error(f"Error checking Lightning invoice status: {str(e)}")
            return {
                'status': invoice.status,
                'paid_at': invoice.paid_at.isoformat() if invoice.paid_at else None,
                'amount_sats': invoice.amount_sats
            }
    
    def get_lightning_payment_history(self, user: BitzappUser, limit: int = 10) -> list:
        """
        Get user's Lightning payment history
        """
        try:
            # Get Lightning invoices
            invoices = LightningInvoice.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            # Get Lightning payments
            payments = LightningPayment.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            history = []
            
            # Add invoices to history
            for invoice in invoices:
                history.append({
                    'type': 'lightning_invoice',
                    'amount_sats': invoice.amount_sats,
                    'amount_btc': float(invoice.amount_btc),
                    'amount_ngn': float(invoice.amount_ngn),
                    'status': invoice.status,
                    'payment_request': invoice.payment_request[:50] + '...' if len(invoice.payment_request) > 50 else invoice.payment_request,
                    'created_at': invoice.created_at.isoformat()
                })
            
            # Add payments to history
            for payment in payments:
                history.append({
                    'type': 'lightning_payment',
                    'amount_sats': payment.amount_sats,
                    'amount_btc': float(payment.amount_btc),
                    'amount_ngn': float(payment.amount_ngn),
                    'status': payment.status,
                    'payment_request': payment.payment_request[:50] + '...' if len(payment.payment_request) > 50 else payment.payment_request,
                    'created_at': payment.created_at.isoformat()
                })
            
            # Sort by creation date
            history.sort(key=lambda x: x['created_at'], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting Lightning payment history for {user.phone_number}: {str(e)}")
            return []
