from django.db import models
from decimal import Decimal
import hashlib
import secrets


class BitcoinAddress(models.Model):
    """
    Bitcoin address management for users
    Each user can have multiple addresses for receiving Bitcoin
    """
    user = models.ForeignKey('core.BitzappUser', on_delete=models.CASCADE, related_name='bitcoin_addresses')
    address = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=200, help_text="Encrypted private key")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Bitcoin Address"
        verbose_name_plural = "Bitcoin Addresses"
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.address[:10]}..."


class WalletBalance(models.Model):
    """
    Track wallet balance history for auditing
    """
    wallet = models.ForeignKey('core.BitcoinWallet', on_delete=models.CASCADE, related_name='balance_history')
    balance_btc = models.DecimalField(max_digits=20, decimal_places=8)
    balance_ngn = models.DecimalField(max_digits=15, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Wallet Balance"
        verbose_name_plural = "Wallet Balances"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.phone_number} - {self.balance_btc} BTC"


class BitcoinTransaction(models.Model):
    """
    Bitcoin blockchain transaction details
    Links to our internal Transaction model
    """
    transaction = models.OneToOneField('core.Transaction', on_delete=models.CASCADE, related_name='bitcoin_details')
    tx_hash = models.CharField(max_length=100, unique=True, help_text="Bitcoin transaction hash")
    confirmations = models.IntegerField(default=0)
    block_height = models.IntegerField(null=True, blank=True)
    fee_btc = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0.00000000'))
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bitcoin Transaction"
        verbose_name_plural = "Bitcoin Transactions"
    
    def __str__(self):
        return f"{self.tx_hash[:10]}... - {self.transaction.amount_btc} BTC"
