"""
Bitcoin wallet services for Bitzapp
Handles Bitcoin address generation, balance management, and transactions
"""
import hashlib
import secrets
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from core.models import BitzappUser, BitcoinWallet, Transaction, ExchangeRate
from wallet.models import BitcoinAddress, WalletBalance, BitcoinTransaction

logger = logging.getLogger('bitzapp')


class BitcoinWalletService:
    """
    Service for managing Bitcoin wallets and transactions
    Supports both custodial and non-custodial wallets
    """
    
    def __init__(self):
        self.network = getattr(settings, 'BITCOIN_NETWORK', 'testnet')
        self.bitnob_api_key = getattr(settings, 'BITNOB_API_KEY', '')
        self.bitnob_base_url = getattr(settings, 'BITNOB_BASE_URL', 'https://api.bitnob.com')
    
    def create_wallet_for_user(self, user: BitzappUser, wallet_type: str = 'custodial') -> BitcoinWallet:
        """
        Create a new Bitcoin wallet for a user
        """
        try:
            if wallet_type == 'custodial':
                return self._create_custodial_wallet(user)
            elif wallet_type == 'non_custodial':
                return self._create_non_custodial_wallet(user)
            else:
                raise ValueError(f"Invalid wallet type: {wallet_type}")
                
        except Exception as e:
            logger.error(f"Error creating wallet for user {user.phone_number}: {str(e)}")
            raise
    
    def _create_custodial_wallet(self, user: BitzappUser) -> BitcoinWallet:
        """
        Create a custodial wallet (we control private keys)
        """
        # Generate Bitcoin address and private key
        bitcoin_address, private_key = self._generate_bitcoin_address()
        
        # Create wallet
        wallet = BitcoinWallet.objects.create(
            user=user,
            wallet_type='custodial',
            bitcoin_address=bitcoin_address,
            private_key=self._encrypt_private_key(private_key)
        )
        
        # Create Bitcoin address record
        BitcoinAddress.objects.create(
            user=user,
            address=bitcoin_address,
            private_key=self._encrypt_private_key(private_key),
            is_active=True
        )
        
        logger.info(f"Created custodial Bitcoin wallet for user {user.phone_number}")
        return wallet
    
    def _create_non_custodial_wallet(self, user: BitzappUser) -> dict:
        """
        Create a non-custodial wallet (user controls private keys)
        """
        try:
            from mnemonic import Mnemonic
            import hashlib
            
            # Check if user already has a wallet
            try:
                existing_wallet = BitcoinWallet.objects.get(user=user)
                if existing_wallet.wallet_type == 'non_custodial':
                    # Return existing non-custodial wallet info
                    return {
                        'wallet': existing_wallet,
                        'seed_phrase': 'EXISTING_WALLET',  # Don't expose existing seed phrase
                        'bitcoin_address': existing_wallet.bitcoin_address
                    }
                else:
                    raise ValueError("User already has a custodial wallet. Cannot create non-custodial wallet.")
            except BitcoinWallet.DoesNotExist:
                pass  # No existing wallet, continue with creation
            
            # Generate 12-word seed phrase
            mnemo = Mnemonic("english")
            seed_phrase = mnemo.generate(strength=128)
            
            # Generate Bitcoin address from seed phrase
            bitcoin_address = self._generate_address_from_seed(seed_phrase)
            
            # Create wallet record (no private key stored)
            wallet = BitcoinWallet.objects.create(
                user=user,
                wallet_type='non_custodial',
                bitcoin_address=bitcoin_address,
                private_key="",  # Empty for non-custodial
                seed_phrase_hash=hashlib.sha256(seed_phrase.encode()).hexdigest()
            )
            
            logger.info(f"Created non-custodial Bitcoin wallet for user {user.phone_number}")
            
            return {
                'wallet': wallet,
                'seed_phrase': seed_phrase,
                'bitcoin_address': bitcoin_address
            }
            
        except Exception as e:
            logger.error(f"Error creating non-custodial wallet: {str(e)}")
            raise
    
    def _generate_bitcoin_address(self) -> tuple:
        """
        Generate a new Bitcoin address and private key
        For production, use proper Bitcoin libraries like bitcoinlib
        This is a simplified version for demo purposes
        """
        # Generate a random private key (32 bytes)
        private_key = secrets.token_hex(32)
        
        # For demo purposes, create a simple address
        # In production, use proper Bitcoin address generation
        address_hash = hashlib.sha256(private_key.encode()).hexdigest()[:34]
        bitcoin_address = f"bc1{address_hash}"
        
        return bitcoin_address, private_key
    
    def _generate_address_from_seed(self, seed_phrase: str) -> str:
        """
        Generate Bitcoin address from seed phrase
        """
        try:
            # For demo purposes, create a deterministic address from seed phrase
            # In production, use proper Bitcoin libraries
            address_hash = hashlib.sha256(seed_phrase.encode()).hexdigest()[:34]
            bitcoin_address = f"bc1{address_hash}"
            
            return bitcoin_address
            
        except Exception as e:
            logger.error(f"Error generating address from seed: {str(e)}")
            # Fallback to demo address
            address_hash = hashlib.sha256(seed_phrase.encode()).hexdigest()[:34]
            return f"bc1{address_hash}"
    
    def _encrypt_private_key(self, private_key: str) -> str:
        """
        Encrypt private key for storage
        In production, use proper encryption
        """
        # Simple encoding for demo - use proper encryption in production
        return hashlib.sha256(private_key.encode()).hexdigest()
    
    def get_wallet_balance(self, user: BitzappUser) -> dict:
        """
        Get user's wallet balance in BTC and NGN
        """
        try:
            wallet = BitcoinWallet.objects.get(user=user)
            
            # Get current exchange rate
            exchange_rate = self._get_current_exchange_rate()
            
            # Calculate NGN balance
            balance_ngn = wallet.balance_btc * exchange_rate
            
            return {
                'balance_btc': float(wallet.balance_btc),
                'balance_ngn': float(balance_ngn),
                'exchange_rate': float(exchange_rate),
                'bitcoin_address': wallet.bitcoin_address
            }
            
        except BitcoinWallet.DoesNotExist:
            # Create wallet if it doesn't exist
            wallet = self.create_wallet_for_user(user)
            return self.get_wallet_balance(user)
        except Exception as e:
            logger.error(f"Error getting balance for user {user.phone_number}: {str(e)}")
            raise
    
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
            
            # Fetch BTC price in NGN
            response = requests.get(
                f"{self.bitnob_base_url}/api/v1/rates/btc",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                rate = Decimal(str(data.get('rate', 50000000)))
                
                # Save to database
                ExchangeRate.objects.create(
                    btc_to_ngn=rate,
                    source='bitnob'
                )
                
                return rate
            else:
                logger.error(f"Bitnob API error: {response.status_code}")
                return Decimal('50000000')
                
        except Exception as e:
            logger.error(f"Error fetching exchange rate from API: {str(e)}")
            return Decimal('50000000')
    
    def import_wallet_from_seed(self, user: BitzappUser, seed_phrase: str) -> dict:
        """
        Import existing wallet from seed phrase
        """
        try:
            from mnemonic import Mnemonic
            import hashlib
            
            # Validate seed phrase
            mnemo = Mnemonic("english")
            if not mnemo.check(seed_phrase):
                raise ValueError("Invalid seed phrase")
            
            # Generate Bitcoin address from seed phrase
            bitcoin_address = self._generate_address_from_seed(seed_phrase)
            
            # Check if wallet already exists
            try:
                existing_wallet = BitcoinWallet.objects.get(user=user)
                if existing_wallet.wallet_type == 'non_custodial':
                    # Update existing non-custodial wallet
                    existing_wallet.bitcoin_address = bitcoin_address
                    existing_wallet.seed_phrase_hash = hashlib.sha256(seed_phrase.encode()).hexdigest()
                    existing_wallet.save()
                    wallet = existing_wallet
                else:
                    raise ValueError("User already has a custodial wallet")
            except BitcoinWallet.DoesNotExist:
                # Create new non-custodial wallet
                wallet = BitcoinWallet.objects.create(
                    user=user,
                    wallet_type='non_custodial',
                    bitcoin_address=bitcoin_address,
                    private_key="",  # Empty for non-custodial
                    seed_phrase_hash=hashlib.sha256(seed_phrase.encode()).hexdigest()
                )
            
            # Get balance from blockchain
            balance = self._get_balance_from_blockchain(bitcoin_address)
            wallet.balance_btc = balance
            wallet.save()
            
            logger.info(f"Imported non-custodial wallet for user {user.phone_number}")
            
            return {
                'wallet': wallet,
                'bitcoin_address': bitcoin_address,
                'balance': balance
            }
            
        except Exception as e:
            logger.error(f"Error importing wallet: {str(e)}")
            raise
    
    def send_bitcoin(self, from_user: BitzappUser, to_address: str, amount_btc: Decimal, description: str = "", seed_phrase: str = None) -> Transaction:
        """
        Send Bitcoin from one user to another address
        Supports both custodial and non-custodial wallets
        """
        try:
            with transaction.atomic():
                # Get sender's wallet
                sender_wallet = BitcoinWallet.objects.get(user=from_user)
                
                # Check if user has sufficient balance
                if sender_wallet.balance_btc < amount_btc:
                    raise ValueError("Insufficient Bitcoin balance")
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    user=from_user,
                    transaction_type='transfer',
                    amount_btc=amount_btc,
                    from_address=sender_wallet.bitcoin_address,
                    to_address=to_address,
                    description=description,
                    status='pending'
                )
                
                # Handle transaction based on wallet type
                if sender_wallet.is_custodial:
                    # Custodial wallet - we control the private key
                    tx_hash = self._send_custodial_transaction(sender_wallet, to_address, amount_btc)
                elif sender_wallet.is_non_custodial:
                    # Non-custodial wallet - user provides seed phrase
                    if not seed_phrase:
                        raise ValueError("Seed phrase required for non-custodial wallet")
                    tx_hash = self._send_non_custodial_transaction(seed_phrase, to_address, amount_btc)
                else:
                    raise ValueError("Unknown wallet type")
                
                # Update transaction with hash
                transaction_obj.bitcoin_tx_hash = tx_hash
                transaction_obj.status = 'completed'
                transaction_obj.completed_at = transaction_obj.updated_at
                transaction_obj.save()
                
                # Update wallet balance
                sender_wallet.balance_btc -= amount_btc
                sender_wallet.save()
                
                # Create balance history record
                WalletBalance.objects.create(
                    wallet=sender_wallet,
                    balance_btc=sender_wallet.balance_btc,
                    balance_ngn=sender_wallet.balance_ngn,
                    exchange_rate=self._get_current_exchange_rate()
                )
                
                logger.info(f"Bitcoin sent: {amount_btc} BTC from {from_user.phone_number} to {to_address}")
                return transaction_obj
                
        except Exception as e:
            logger.error(f"Error sending Bitcoin: {str(e)}")
            raise
    
    def _send_custodial_transaction(self, wallet: BitcoinWallet, to_address: str, amount_btc: Decimal) -> str:
        """
        Send transaction from custodial wallet
        """
        try:
            # In production, use the stored private key to sign transaction
            # For demo, create a mock transaction hash
            tx_data = f"{wallet.bitcoin_address}{to_address}{amount_btc}"
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
            
            logger.info(f"Custodial transaction: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error sending custodial transaction: {str(e)}")
            raise
    
    def _send_non_custodial_transaction(self, seed_phrase: str, to_address: str, amount_btc: Decimal) -> str:
        """
        Send transaction from non-custodial wallet using seed phrase
        """
        try:
            # For demo purposes, create a mock transaction hash
            # In production, use proper Bitcoin libraries to sign and broadcast
            tx_data = f"{seed_phrase}{to_address}{amount_btc}"
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
            
            logger.info(f"Non-custodial transaction: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error sending non-custodial transaction: {str(e)}")
            raise
    
    def _get_balance_from_blockchain(self, address: str) -> Decimal:
        """
        Get balance directly from blockchain
        """
        try:
            # In production, implement with blockchain API (BlockCypher, Blockstream, etc.)
            # For demo, return 0
            return Decimal('0.00000000')
            
        except Exception as e:
            logger.error(f"Error getting balance from blockchain: {str(e)}")
            return Decimal('0.00000000')
    
    def receive_bitcoin(self, user: BitzappUser, amount_btc: Decimal, from_address: str, tx_hash: str) -> Transaction:
        """
        Process incoming Bitcoin transaction
        """
        try:
            with transaction.atomic():
                # Get or create user's wallet
                wallet, created = BitcoinWallet.objects.get_or_create(
                    user=user,
                    defaults={
                        'bitcoin_address': self._generate_bitcoin_address()[0],
                        'private_key': self._encrypt_private_key(self._generate_bitcoin_address()[1])
                    }
                )
                
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    user=user,
                    transaction_type='receive',
                    amount_btc=amount_btc,
                    from_address=from_address,
                    to_address=wallet.bitcoin_address,
                    bitcoin_tx_hash=tx_hash,
                    status='completed'
                )
                
                # Update wallet balance
                wallet.balance_btc += amount_btc
                wallet.save()
                
                # Create balance history record
                WalletBalance.objects.create(
                    wallet=wallet,
                    balance_btc=wallet.balance_btc,
                    balance_ngn=wallet.balance_ngn,
                    exchange_rate=self._get_current_exchange_rate()
                )
                
                logger.info(f"Bitcoin received: {amount_btc} BTC for {user.phone_number}")
                return transaction_obj
                
        except Exception as e:
            logger.error(f"Error receiving Bitcoin: {str(e)}")
            raise
    
    def get_transaction_history(self, user: BitzappUser, limit: int = 10) -> list:
        """
        Get user's transaction history
        """
        try:
            transactions = Transaction.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'id': str(tx.id),
                    'type': tx.transaction_type,
                    'status': tx.status,
                    'amount_btc': float(tx.amount_btc),
                    'amount_ngn': float(tx.amount_ngn) if tx.amount_ngn else None,
                    'description': tx.description,
                    'created_at': tx.created_at.isoformat(),
                    'completed_at': tx.completed_at.isoformat() if tx.completed_at else None
                }
                for tx in transactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting transaction history for {user.phone_number}: {str(e)}")
            return []
