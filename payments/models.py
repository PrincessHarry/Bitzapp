from django.db import models
from decimal import Decimal
import uuid


class BillPayment(models.Model):
    """
    Bill payment transactions
    Links Bitcoin payments to Naira bill payments
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    transaction = models.OneToOneField('core.Transaction', on_delete=models.CASCADE, related_name='bill_payment')
    provider = models.ForeignKey('core.BillProvider', on_delete=models.CASCADE, related_name='bill_payments')
    
    # Bill details
    customer_reference = models.CharField(max_length=100, help_text="Customer reference (phone, account number, etc.)")
    bill_reference = models.CharField(max_length=100, help_text="Bill reference number")
    amount_ngn = models.DecimalField(max_digits=15, decimal_places=2, help_text="Bill amount in Naira")
    amount_btc = models.DecimalField(max_digits=20, decimal_places=8, help_text="Bitcoin amount paid")
    
    # Payment processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_transaction_id = models.CharField(max_length=100, blank=True, help_text="Provider's transaction ID")
    provider_response = models.TextField(blank=True, help_text="Provider's response data")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Bill Payment"
        verbose_name_plural = "Bill Payments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.name} - {self.customer_reference} - {self.amount_ngn} NGN"


class NairaDeposit(models.Model):
    """
    Naira deposits that get converted to Bitcoin
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey('core.BitzappUser', on_delete=models.CASCADE, related_name='naira_deposits')
    amount_ngn = models.DecimalField(max_digits=15, decimal_places=2, help_text="Deposit amount in Naira")
    amount_btc = models.DecimalField(max_digits=20, decimal_places=8, help_text="Bitcoin amount received")
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Exchange rate used")
    
    # Payment method details
    payment_method = models.CharField(max_length=50, help_text="Payment method (bank_transfer, card, etc.)")
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Payment reference")
    provider_transaction_id = models.CharField(max_length=100, blank=True, help_text="Provider transaction ID")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Naira Deposit"
        verbose_name_plural = "Naira Deposits"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.phone_number} - {self.amount_ngn} NGN → {self.amount_btc} BTC"


class ExchangeRateHistory(models.Model):
    """
    Historical exchange rate data
    """
    btc_to_ngn = models.DecimalField(max_digits=15, decimal_places=2)
    source = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Exchange Rate History"
        verbose_name_plural = "Exchange Rate History"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.created_at} - 1 BTC = {self.btc_to_ngn} NGN ({self.source})"


class NairaWithdrawal(models.Model):
    """
    Naira withdrawal requests (Bitcoin to Nigerian bank account)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey('core.BitzappUser', on_delete=models.CASCADE, related_name='naira_withdrawals')
    amount_btc = models.DecimalField(max_digits=20, decimal_places=8, help_text="Bitcoin amount to withdraw")
    amount_ngn = models.DecimalField(max_digits=15, decimal_places=2, help_text="Naira amount to receive")
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Exchange rate used")
    
    # Bank account details
    bank_account_number = models.CharField(max_length=20, help_text="Nigerian bank account number")
    bank_name = models.CharField(max_length=100, help_text="Bank name")
    account_name = models.CharField(max_length=100, help_text="Account holder name")
    
    # Provider details
    provider_transaction_id = models.CharField(max_length=100, blank=True, help_text="Provider transaction ID")
    provider_response = models.TextField(blank=True, help_text="Provider response")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Naira Withdrawal"
        verbose_name_plural = "Naira Withdrawals"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone_number} - {self.amount_btc} BTC → ₦{self.amount_ngn}"
