from django.contrib import admin
from .models import BitzappUser, BitcoinWallet, Transaction, ExchangeRate, BillProvider


@admin.register(BitzappUser)
class BitzappUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['phone_number', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BitcoinWallet)
class BitcoinWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'bitcoin_address', 'balance_btc', 'balance_ngn', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__phone_number', 'bitcoin_address']
    readonly_fields = ['created_at', 'updated_at', 'balance_ngn']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'status', 'amount_btc', 'amount_ngn', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['user__phone_number', 'bitcoin_tx_hash', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['btc_to_ngn', 'source', 'created_at']
    list_filter = ['source', 'created_at']
    readonly_fields = ['created_at']


@admin.register(BillProvider)
class BillProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'bill_type', 'provider_code', 'is_active']
    list_filter = ['bill_type', 'is_active']
    search_fields = ['name', 'bill_type', 'provider_code']
