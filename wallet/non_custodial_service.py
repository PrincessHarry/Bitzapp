"""
Non-custodial Bitcoin wallet service for Bitzapp
Users control their own private keys through secure seed phrases
"""
import hashlib
import secrets
import logging
from mnemonic import Mnemonic
from bitcoinlib import HDWallet
from decimal import Decimal
from django.conf import settings
from core.models import BitzappUser, Transaction

logger = logging.getLogger('bitzapp')


class NonCustodialWalletService:
    """
    Non-custodial wallet service where users control their private keys
    """
    
    def __init__(self):
        self.network = getattr(settings, 'BITCOIN_NETWORK', 'testnet')
        self.mnemo = Mnemonic("english")
    
    def create_wallet_for_user(self, user: BitzappUser) -> dict:
        """
        Generate a new wallet with seed phrase for user
        Returns seed phrase - user must store it safely
        """
        try:
            # Generate 12-word seed phrase
            seed_phrase = self.mnemo.generate(strength=128)
            
            # Create HD wallet from seed
            wallet = HDWallet.create(
                name=f"bitzapp_{user.phone_number}",
                keys=seed_phrase,
                network=self.network
            )
            
            # Get the first Bitcoin address
            bitcoin_address = wallet.get_key().address
            
            # Store only PUBLIC information in our database
            from core.models import BitcoinWallet
            user_wallet = BitcoinWallet.objects.create(
                user=user,
                bitcoin_address=bitcoin_address,
                private_key="",  # Empty - we don't store private keys!
                balance_btc=Decimal('0.00000000')
            )
            
            logger.info(f"Created non-custodial wallet for user {user.phone_number}")
            
            return {
                'wallet': user_wallet,
                'seed_phrase': seed_phrase,
                'bitcoin_address': bitcoin_address,
                'warning': 'CRITICAL: Store this seed phrase safely. We cannot recover it!'
            }
            
        except Exception as e:
            logger.error(f"Error creating non-custodial wallet: {str(e)}")
            raise
    
    def import_wallet_from_seed(self, user: BitzappUser, seed_phrase: str) -> dict:
        """
        Import existing wallet from user's seed phrase
        """
        try:
            # Validate seed phrase
            if not self.mnemo.check(seed_phrase):
                raise ValueError("Invalid seed phrase")
            
            # Create HD wallet from seed
            wallet = HDWallet.create(
                name=f"bitzapp_{user.phone_number}",
                keys=seed_phrase,
                network=self.network
            )
            
            bitcoin_address = wallet.get_key().address
            
            # Update or create wallet record (public info only)
            from core.models import BitcoinWallet
            user_wallet, created = BitcoinWallet.objects.update_or_create(
                user=user,
                defaults={
                    'bitcoin_address': bitcoin_address,
                    'private_key': "",  # Still empty!
                }
            )
            
            # Sync balance from blockchain
            balance = self.get_balance_from_blockchain(bitcoin_address)
            user_wallet.balance_btc = balance
            user_wallet.save()
            
            return {
                'wallet': user_wallet,
                'bitcoin_address': bitcoin_address,
                'balance': balance
            }
            
        except Exception as e:
            logger.error(f"Error importing wallet: {str(e)}")
            raise
    
    def create_transaction(self, user: BitzappUser, to_address: str, 
                          amount_btc: Decimal, seed_phrase: str) -> dict:
        """
        Create transaction using user's seed phrase
        User provides seed phrase temporarily for signing
        """
        try:
            # Validate seed phrase
            if not self.mnemo.check(seed_phrase):
                raise ValueError("Invalid seed phrase")
            
            # Create wallet from seed
            wallet = HDWallet.create(
                name=f"temp_{user.phone_number}",
                keys=seed_phrase,
                network=self.network
            )
            
            # Get current balance
            from_address = wallet.get_key().address
            balance = self.get_balance_from_blockchain(from_address)
            
            if balance < amount_btc:
                raise ValueError("Insufficient balance")
            
            # Create and sign transaction
            tx = wallet.send_to(to_address, int(amount_btc * 100000000))  # Convert to satoshis
            
            # Broadcast to network (implement with blockchain API)
            tx_hash = self.broadcast_transaction(tx.raw)
            
            # Record transaction in our database
            transaction_obj = Transaction.objects.create(
                user=user,
                transaction_type='transfer',
                amount_btc=amount_btc,
                from_address=from_address,
                to_address=to_address,
                bitcoin_tx_hash=tx_hash,
                status='pending'
            )
            
            return {
                'transaction': transaction_obj,
                'tx_hash': tx_hash,
                'status': 'broadcast'
            }
            
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            raise
    
    def get_balance_from_blockchain(self, address: str) -> Decimal:
        """
        Get balance directly from blockchain
        """
        try:
            # Implement with blockchain API (BlockCypher, Blockstream, etc.)
            # For demo, return 0
            return Decimal('0.00000000')
            
        except Exception as e:
            logger.error(f"Error getting balance from blockchain: {str(e)}")
            return Decimal('0.00000000')
    
    def broadcast_transaction(self, raw_tx: str) -> str:
        """
        Broadcast transaction to Bitcoin network
        """
        try:
            # Implement with blockchain API
            # For demo, return mock hash
            return hashlib.sha256(raw_tx.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Error broadcasting transaction: {str(e)}")
            raise
