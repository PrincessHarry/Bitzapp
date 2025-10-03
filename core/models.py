from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class BitzappUser(models.Model):
    """
    Extended user model for Bitzapp users
    Links Django User with WhatsApp phone number and additional profile info
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bitzapp_profile')
    phone_number = models.CharField(max_length=20, unique=True, help_text="WhatsApp phone number")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bitzapp User"
        verbose_name_plural = "Bitzapp Users"
    
    def __str__(self):
        return f"{self.user.username} ({self.phone_number})"


class BitcoinWallet(models.Model):
    """
    Bitcoin wallet for each user
    Supports both custodial and non-custodial wallets
    """
    WALLET_TYPES = [
        ('custodial', 'Custodial'),
        ('non_custodial', 'Non-Custodial'),
    ]
    
    user = models.OneToOneField(BitzappUser, on_delete=models.CASCADE, related_name='bitcoin_wallet')
    wallet_type = models.CharField(max_length=20, choices=WALLET_TYPES, default='custodial')
    bitcoin_address = models.CharField(max_length=100, unique=True, help_text="Bitcoin address for receiving funds")
    private_key = models.CharField(max_length=200, blank=True, help_text="Encrypted private key (empty for non-custodial)")
    seed_phrase_hash = models.CharField(max_length=200, blank=True, help_text="Hash of seed phrase for verification (non-custodial only)")
    balance_btc = models.DecimalField(
        max_digits=20, 
        decimal_places=8, 
        default=Decimal('0.00000000'),
        validators=[MinValueValidator(Decimal('0.00000000'))],
        help_text="Bitcoin balance in BTC"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bitcoin Wallet"
        verbose_name_plural = "Bitcoin Wallets"
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.balance_btc} BTC"
    
    @property
    def balance_ngn(self):
        """Calculate Naira equivalent of Bitcoin balance"""
        # This will be implemented with real-time exchange rate
        # For now, using a placeholder rate
        return self.balance_btc * Decimal('50000000')  # Placeholder: 1 BTC = 50M NGN
    
    @property
    def is_non_custodial(self):
        """Check if wallet is non-custodial"""
        return self.wallet_type == 'non_custodial'
    
    @property
    def is_custodial(self):
        """Check if wallet is custodial"""
        return self.wallet_type == 'custodial'


class Transaction(models.Model):
    """
    Transaction model for all Bitcoin transactions
    Tracks deposits, withdrawals, transfers, and bill payments
    """
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('bill_payment', 'Bill Payment'),
        ('receive', 'Receive'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BitzappUser, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Bitcoin amounts
    amount_btc = models.DecimalField(
        max_digits=20, 
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))],
        help_text="Amount in Bitcoin"
    )
    amount_ngn = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Naira equivalent amount"
    )
    
    # Transaction details
    from_address = models.CharField(max_length=100, blank=True, help_text="Sender Bitcoin address")
    to_address = models.CharField(max_length=100, blank=True, help_text="Recipient Bitcoin address")
    bitcoin_tx_hash = models.CharField(max_length=100, blank=True, help_text="Bitcoin transaction hash")
    
    # For bill payments
    bill_type = models.CharField(max_length=50, blank=True, help_text="Type of bill (electricity, airtime, etc.)")
    bill_reference = models.CharField(max_length=100, blank=True, help_text="Bill reference number")
    merchant_account = models.CharField(max_length=100, blank=True, help_text="Merchant account details")
    
    # Metadata
    description = models.TextField(blank=True, help_text="Transaction description")
    exchange_rate = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="BTC to NGN exchange rate at time of transaction"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.transaction_type} - {self.amount_btc} BTC"


class ExchangeRate(models.Model):
    """
    Store Bitcoin to Naira exchange rates
    Updated periodically from external APIs
    """
    btc_to_ngn = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="1 BTC to NGN rate"
    )
    source = models.CharField(max_length=50, help_text="Rate source (bitnob, mavapay, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"1 BTC = {self.btc_to_ngn} NGN ({self.source})"


class BillProvider(models.Model):
    """
    Bill payment providers and their details
    """
    name = models.CharField(max_length=100, help_text="Provider name (MTN, Airtel, etc.)")
    bill_type = models.CharField(max_length=50, help_text="Type of bill (airtime, electricity, etc.)")
    is_active = models.BooleanField(default=True)
    provider_code = models.CharField(max_length=20, help_text="Provider code for API")
    
    class Meta:
        verbose_name = "Bill Provider"
        verbose_name_plural = "Bill Providers"
    
    def __str__(self):
        return f"{self.name} - {self.bill_type}"
