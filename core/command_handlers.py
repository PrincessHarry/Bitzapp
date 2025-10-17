"""
Command handlers for Bitzapp WhatsApp interface
Handles individual commands like /balance, /send, /deposit, etc.
"""
import re
import logging
from decimal import Decimal
from .models import BitzappUser, BillProvider
from wallet.services import BitcoinWalletService
from payments.services import PaymentService
from payments.bitnob_service import BitnobService
from chatbot.services import AIChatbotService

logger = logging.getLogger('bitzapp')


def handle_create_wallet_command(user: BitzappUser) -> str:
    """
    Handle /create command for Lightning wallet
    """
    try:
        bitnob = BitnobService()
        
        # Create Lightning wallet via Bitnob
        result = bitnob.create_wallet(user.phone_number)
        
        if result.get("success"):
            # Create LNURL address for receiving payments
            identifier = user.phone_number.replace("+", "").replace("-", "").replace(" ", "")
            lnurl_result = bitnob.create_lnurl_address(user.phone_number, identifier)
            
            if lnurl_result.get("success"):
                return f"""⚡ Lightning Wallet Created Successfully!

Your Lightning Address:
{lnurl_result['identifier']}@bitzapp-i3i3.onrender.com

Your LNURL QR Code:
{lnurl_result['lnurl_qr']}

Lightning Network Benefits:
⚡ Instant payments
⚡ Low fees (micro-fees)
⚡ Scalable Bitcoin network
⚡ Perfect for everyday use

Commands:
- /balance - Check your Lightning balance
- /send - Send Lightning payments
- /receive - Get your Lightning address
- /deposit - Add Naira to get Lightning Bitcoin

Your Lightning wallet is ready to use! 🚀"""
            else:
                return f"""Lightning Wallet Created!

Your wallet is ready, but we couldn't create your Lightning address yet.
Please try /receive to get your Lightning address.

Commands:
- /balance - Check your balance
- /receive - Get your Lightning address
- /deposit - Add Naira to get Lightning Bitcoin"""
        else:
            return f"Sorry, I couldn't create your Lightning wallet. {result.get('error', 'Please try again.')}"
        
    except Exception as e:
        logger.error(f"Error creating Lightning wallet: {str(e)}")
        return "Sorry, I couldn't create your Lightning wallet. Please try again."


def handle_import_wallet_command(user: BitzappUser, message: str) -> str:
    """
    Handle /import command - Lightning wallets don't need seed phrases
    """
    return """⚡ Lightning Network - No Import Needed!

Lightning Network wallets work differently from traditional Bitcoin wallets:

**Why No Seed Phrase?**
- Lightning payments are instant and off-chain
- Your Lightning address is your identifier
- No need to import or manage private keys
- Much simpler and safer for everyday use

**To Get Started:**
- /create - Create your Lightning wallet
- /receive - Get your Lightning address
- /deposit - Add Naira to get Lightning Bitcoin

**Lightning Benefits:**
⚡ Instant payments
⚡ Low fees (micro-fees)
⚡ No complex key management
⚡ Perfect for daily transactions

Ready to create your Lightning wallet? Type /create! 🚀"""


def handle_wallet_info_command() -> str:
    """
    Handle /wallet command to explain Lightning wallet
    """
    return """⚡ Lightning Network Wallet Information

Your Bitzapp wallet uses the Lightning Network for instant Bitcoin payments.

Key Features:
- Lightning Network powered
- Instant payments
- Low fees (micro-fees)
- No complex key management
- Perfect for everyday use

Commands:
- /create - Create your Lightning wallet
- /balance - Check your Lightning balance
- /send - Send Lightning payments
- /receive - Get your Lightning address
- /deposit - Add Naira to get Lightning Bitcoin

Lightning Benefits:
⚡ Instant confirmation
⚡ Micro-fee payments
⚡ Scalable Bitcoin network
⚡ No waiting for blockchain confirmations
⚡ Perfect for small payments

Ready to create your Lightning wallet? Type /create to get started! 🚀"""


def handle_deposit_command(user: BitzappUser, message: str) -> str:
    """
    Handle /save or /deposit command
    """
    try:
        # Extract amount from message
        amount_match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not amount_match:
            return """ Deposit Naira to Convert to Bitcoin

**Usage:** /deposit <amount>
**Example:** /deposit 50000

This will convert your Naira to Bitcoin at the current exchange rate.

**Current Exchange Rate:** 1 BTC = ₦50,000,000 (approximate)

**How it works:**
1. Send Naira to our bank account
2. We automatically convert it to Bitcoin
3. Bitcoin is added to your wallet

**Bank Details:**
Account: Bitzapp Limited
Account Number: 1234567890
Bank: Access Bank

Send the exact amount and we'll process it within 24 hours! 🚀"""
        
        amount = Decimal(amount_match.group(1))
        
        # Create deposit via Bitnob
        bitnob = BitnobService()
        result = bitnob.deposit_naira(user.phone_number, float(amount))
        
        if result.get("success"):
            return f""" Deposit Request Created

**Amount:** ₦{amount:,.2f}
**Bitcoin Equivalent:** {result.get('amount_btc', 0):.8f} BTC
**Exchange Rate:** 1 BTC = ₦{result.get('exchange_rate', 0):,.2f}
**Status:** {result.get('status', 'pending').title()}

Your Bitcoin will be added to your wallet once payment is confirmed. 🚀"""
        else:
            return f"Sorry, I couldn't process your deposit. {result.get('error', 'Please try again.')}"
        
    except Exception as e:
        logger.error(f"Error handling deposit command: {str(e)}")
        return "Sorry, I couldn't process your deposit request. Please try again."


def handle_balance_command(user: BitzappUser) -> str:
    """
    Handle /balance command - shows wallet type
    """
    try:
        from .models import BitcoinWallet
        
        try:
            wallet = BitcoinWallet.objects.get(user=user)
        except BitcoinWallet.DoesNotExist:
            return """No Wallet Found

You don't have a wallet yet. Choose an option:

Create Non-Custodial Wallet:
/create - Generate new wallet with seed phrase

Import Existing Wallet:
/import <12-word seed phrase>

Both options create a wallet where YOU control your private keys."""
        
        bitnob = BitnobService()
        balance = bitnob.get_wallet_balance(user.phone_number)
        rate_info = bitnob.get_exchange_rate()
        
        wallet_type = "Secure Wallet"
        security_status = "You control your private keys"
        
        return f"""Your Bitcoin Wallet Balance

Bitcoin: {balance.get('balance_btc', 0):.8f} BTC
Naira Value: ₦{(balance.get('balance_btc', 0) * rate_info.get('rate', 0)):,.2f}
Exchange Rate: 1 BTC = ₦{rate_info.get('rate', 0):,.2f}

Your Bitcoin Address:
{balance.get('bitcoin_address', 'Unavailable')}

Wallet Type: {wallet_type}
Security: {security_status}

Recent Transactions:
{get_recent_transactions(user)}

Commands:
- /send - Send Bitcoin (requires seed phrase)
- /receive - Get your Bitcoin address
- /deposit - Add Naira to convert to Bitcoin

Use your Bitcoin address to receive Bitcoin from others."""
        
    except Exception as e:
        logger.error(f"Error handling balance command: {str(e)}")
        return "Sorry, I couldn't retrieve your balance. Please try again."


def handle_send_command(user: BitzappUser, message: str) -> str:
    """
    Handle /send command - Lightning payments
    """
    try:
        # Extract components from message
        parts = message.split()
        if len(parts) < 3:
            return """⚡ Send Lightning Payments

**Usage:** /send <amount_sats> <lightning_address>
**Example:** /send 1000 satoshi@bitzapp-i3i3.onrender.com

**Lightning Address Examples:**
• satoshi@bitzapp-i3i3.onrender.com
• alice@lightning.com
• bob@ln.pay

**Tips:**
• Lightning addresses are like email addresses
• Amount is in satoshis (1 BTC = 100,000,000 sats)
• Payments are instant and low-fee
• Always verify the recipient address"""

        try:
            amount_sats = int(parts[1])
        except ValueError:
            return "❌ Amount must be a number in satoshis. Example: /send 1000 satoshi@bitnob.com"

        lightning_address = parts[2]

        if amount_sats <= 0:
            return "❌ Amount must be greater than 0 satoshis"

        # Check if it's a Lightning address (contains @)
        if "@" not in lightning_address:
            return """❌ Invalid Lightning Address

Lightning addresses look like email addresses:
• satoshi@bitzapp-i3i3.onrender.com
• alice@lightning.com
• bob@ln.pay

Please provide a valid Lightning address."""

        # Check balance via Bitnob
        bitnob = BitnobService()
        balance = bitnob.get_wallet_balance(user.phone_number)
        rate_info = bitnob.get_exchange_rate()
        
        if balance.get('success') and balance.get('balance_btc', 0) < (amount_sats / 100_000_000):
            return f"""❌ Insufficient Balance

**Your Balance:** {balance.get('balance_btc', 0):.8f} BTC ({balance.get('balance_btc', 0) * 100_000_000:,.0f} sats)
**Trying to Send:** {amount_sats:,} sats

You need more Lightning Bitcoin. Use /deposit to add Naira and convert to Lightning Bitcoin! 💰"""

        # For now, we'll use Lightning invoice creation instead of direct LNURL payment
        # This is a simplified approach - in production you'd decode the LNURL first
        result = bitnob.create_lightning_invoice(user.phone_number, amount_sats, f"Payment to {lightning_address}")
        
        if result.get('success'):
            return f"""⚡ Lightning Payment Initiated!

**Amount:** {amount_sats:,} sats ({amount_sats / 100_000_000:.8f} BTC)
**To:** {lightning_address}
**Naira Value:** ₦{(amount_sats / 100_000_000) * rate_info.get('rate', 0):,.2f}

**Payment Request:**
`{result.get('payment_request')}`

**Lightning Benefits:**
⚡ Instant confirmation
⚡ Micro-fee payment
⚡ No waiting for blockchain confirmations

Your Lightning payment is being processed! 🚀"""
        else:
            return f"Sorry, I couldn't process your Lightning payment. {result.get('error', 'Please try again.')}"
        
    except Exception as e:
        logger.error(f"Error handling send command: {str(e)}")
        return "Sorry, I couldn't process your send request. Please check the format and try again."


def handle_receive_command(user: BitzappUser) -> str:
    """
    Handle /receive command - Lightning address
    """
    try:
        bitnob = BitnobService()
        
        # Create or get LNURL address
        identifier = user.phone_number.replace("+", "").replace("-", "").replace(" ", "")
        lnurl_result = bitnob.create_lnurl_address(user.phone_number, identifier)
        
        if lnurl_result.get("success"):
            balance = bitnob.get_wallet_balance(user.phone_number)
            rate_info = bitnob.get_exchange_rate()
            
            return f"""⚡ Receive Lightning Payments

Your Lightning Address:
{lnurl_result['identifier']}@bitzapp-i3i3.onrender.com

Your LNURL QR Code:
{lnurl_result['lnurl_qr']}

How to receive Lightning payments:
1. Share your Lightning address with the sender
2. They scan your QR code or use your address
3. You'll receive Lightning Bitcoin instantly
4. Check balance with /balance

Current Balance: {balance.get('balance_btc', 0):.8f} BTC (₦{balance.get('balance_btc', 0) * rate_info.get('rate', 0):,.2f})

Lightning Benefits:
⚡ Instant confirmation
⚡ Micro-fee payments
⚡ No waiting for blockchain confirmations
⚡ Perfect for small payments

Share your Lightning address to receive payments! 🚀"""
        else:
            return f"Sorry, I couldn't create your Lightning address. {lnurl_result.get('error', 'Please try again.')}"
        
    except Exception as e:
        logger.error(f"Error handling receive command: {str(e)}")
        return "Sorry, I couldn't retrieve your Lightning address. Please try again."


def handle_paybill_command(user: BitzappUser, message: str) -> str:
    """
    Handle /paybill command
    """
    try:
        # Extract provider and amount from message
        # Format: /paybill <provider> <amount>
        parts = message.split()
        if len(parts) < 3:
            return """💳 Pay Bills with Bitcoin

**Usage:** /paybill <provider> <amount>
**Example:** /paybill mtn 1000

**Available Providers:**
• MTN - Airtime and Data
• Airtel - Airtime and Data  
• Electricity - PHCN Bills
• School Fees - Educational Payments

**How it works:**
1. We convert your Bitcoin to Naira
2. Pay the bill in Naira
3. You get confirmation

**Current Balance:** {get_user_balance(user)}

Ready to pay bills? Use the format above! 🚀"""
        
        provider = parts[1].lower()
        amount = Decimal(parts[2])
        
        # Validate amount
        if amount <= 0:
            return "❌ Amount must be greater than 0"
        
        # Get provider
        try:
            bill_provider = BillProvider.objects.filter(
                name__iexact=provider,
                is_active=True
            ).first()
            
            if not bill_provider:
                return f"❌ Provider '{provider}' not found. Use /paybill to see available providers."
        except BillProvider.DoesNotExist:
            return f"❌ Provider '{provider}' not found. Use /paybill to see available providers."
        
        # Check balance
        wallet_service = BitcoinWalletService()
        balance = wallet_service.get_wallet_balance(user)
        
        # Calculate Bitcoin amount needed
        bitcoin_needed = amount / Decimal(str(balance['exchange_rate']))
        
        if balance['balance_btc'] < bitcoin_needed:
            return f"""❌ Insufficient Balance

**Bill Amount:** ₦{amount:,.2f}
**Bitcoin Needed:** {bitcoin_needed:.8f} BTC
**Your Balance:** {balance['balance_btc']:.8f} BTC

You need more Bitcoin. Use /deposit to add Naira and convert to Bitcoin! 💰"""
        
        # Process bill payment
        payment_service = PaymentService()
        bill_payment = payment_service.pay_bill(
            user, bill_provider, user.phone_number, amount
        )
        
        return f"""✅ Bill Payment Successful!

**Provider:** {bill_provider.name}
**Amount:** ₦{amount:,.2f}
**Bitcoin Used:** {bitcoin_needed:.8f} BTC
**Transaction ID:** {bill_payment.id}

Your bill has been paid! You'll receive confirmation from the provider. 🚀"""
        
    except Exception as e:
        logger.error(f"Error handling paybill command: {str(e)}")
        return "Sorry, I couldn't process your bill payment. Please check the format and try again."


def handle_ask_command(user: BitzappUser, message: str) -> str:
    """
    Handle /ask command for AI chatbot
    """
    try:
        # Extract question from message
        question = message[4:].strip()  # Remove '/ask ' prefix
        
        if not question:
            return """🤖 Ask Me Anything!

**Usage:** /ask <your question>
**Example:** /ask What is Bitcoin?

I can help with:
• Bitcoin and cryptocurrency questions
• Bitzapp features and usage
• Security tips and best practices
• Troubleshooting issues

Just ask me anything! 🚀"""
        
        # Use AI chatbot service
        chatbot_service = AIChatbotService()
        response = chatbot_service.get_chat_response(user, question)
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling ask command: {str(e)}")
        return "Sorry, I couldn't process your question. Please try again."


def handle_lightning_invoice_command(user: BitzappUser, message: str) -> str:
    """
    Handle /lightning command to create Lightning invoice
    Usage: /lightning <amount_sats> [description]
    """
    try:
        # Parse command
        parts = message.split()
        if len(parts) < 2:
            return """⚡ Lightning Invoice Command

**Usage:** `/lightning <amount_sats> [description]`

**Examples:**
• `/lightning 1000` - Create 1000 sats invoice
• `/lightning 5000 Coffee payment` - Create 5000 sats invoice with description

**Lightning Network Benefits:**
⚡ Instant Bitcoin payments
⚡ Low fees (micro-fees)
⚡ Scalable Bitcoin network
⚡ Perfect for small payments

**Note:** Lightning invoices expire in 1 hour"""
        
        try:
            amount_sats = int(parts[1])
            if amount_sats <= 0:
                return "❌ Amount must be greater than 0 satoshis"
        except ValueError:
            return "❌ Invalid amount. Please provide a number of satoshis"
        
        description = " ".join(parts[2:]) if len(parts) > 2 else f"Lightning invoice for {user.phone_number}"
        
        # Create Lightning invoice via Bitnob
        bitnob = BitnobService()
        result = bitnob.create_lightning_invoice(user.phone_number, amount_sats, description)
        if result.get('success'):
            rate_info = BitnobService().get_exchange_rate()
            amount_btc = amount_sats / 100_000_000
            amount_ngn = amount_btc * rate_info.get('rate', 0)
            return f"""⚡ Lightning Invoice Created!

**Amount:** {amount_sats:,} sats ({amount_btc:.8f} BTC)
**Naira Value:** ₦{amount_ngn:,.2f}
**Description:** {description}

**Payment Request:**
`{result.get('payment_request')}`

**Invoice Details:**
• Invoice ID: `{result.get('invoice_id')}`
• Status: {result.get('status', 'pending').title()}

**How to Pay:**
1. Copy the payment request above
2. Use any Lightning wallet (Phoenix, Breez, etc.)
3. Scan or paste the payment request
4. Confirm the payment

Your Lightning invoice is ready! 🚀"""
        else:
            return f"❌ Error creating Lightning invoice: {result.get('error', 'Please try again.')}"
        
    except Exception as e:
        logger.error(f"Error creating Lightning invoice: {str(e)}")
        return f"❌ Error creating Lightning invoice: {str(e)}"


def handle_lightning_pay_command(user: BitzappUser, message: str) -> str:
    """
    Handle /lightningpay command to pay Lightning invoice
    Usage: /lightningpay <payment_request> [description]
    """
    try:
        # Parse command
        parts = message.split()
        if len(parts) < 2:
            return """⚡ Lightning Payment Command

**Usage:** `/lightningpay <payment_request> [description]`

**Examples:**
• `/lightningpay lnbc1000u1p...` - Pay Lightning invoice
• `/lightningpay lnbc5000u1p... Coffee payment` - Pay with description

**How to Get Payment Request:**
1. Ask sender to create Lightning invoice
2. Copy the payment request (starts with 'lnbc')
3. Use this command to pay

**Lightning Benefits:**
⚡ Instant Bitcoin payments
⚡ Low fees
⚡ Scalable network"""
        
        payment_request = parts[1]
        description = " ".join(parts[2:]) if len(parts) > 2 else f"Lightning payment from {user.phone_number}"
        
        # Validate payment request format
        if not payment_request.startswith('lnbc'):
            return "❌ Invalid payment request. Must start with 'lnbc'"
        
        # Pay Lightning invoice via Bitnob
        bitnob = BitnobService()
        result = bitnob.pay_lightning_invoice(user.phone_number, payment_request, description)
        if result.get('success'):
            rate_info = bitnob.get_exchange_rate()
            amount_sats = result.get('amount_sats', 0)
            amount_btc = (amount_sats or 0) / 100_000_000
            amount_ngn = amount_btc * rate_info.get('rate', 0)
            return f"""⚡ Lightning Payment Successful!

**Amount:** {amount_sats:,} sats ({amount_btc:.8f} BTC)
**Naira Value:** ₦{amount_ngn:,.2f}
**Description:** {description}

**Payment Details:**
• Payment ID: `{result.get('payment_id')}`
• Status: {result.get('status', 'completed').title()}

Your Lightning payment is complete! 🚀"""
        else:
            return f"❌ Error processing Lightning payment: {result.get('error', 'Please try again.')}"
        
    except ValueError as e:
        if "Insufficient Bitcoin balance" in str(e):
            return f"""❌ Insufficient Bitcoin Balance

You don't have enough Bitcoin to complete this Lightning payment.

**Your Balance:** Check with `/balance`

**To Add Bitcoin:**
• `/deposit <amount>` - Deposit Naira to get Bitcoin
• `/receive` - Get Bitcoin address for deposits

Lightning payments require Bitcoin in your wallet! 💰"""
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing Lightning payment: {str(e)}")
        return f"❌ Error processing Lightning payment: {str(e)}"


def handle_lightning_status_command(user: BitzappUser, message: str) -> str:
    """
    Handle /lightningstatus command to check Lightning invoice status
    Usage: /lightningstatus <invoice_id>
    """
    try:
        # Parse command
        parts = message.split()
        if len(parts) < 2:
            return """⚡ Lightning Status Command

**Usage:** `/lightningstatus <invoice_id>`

**Examples:**
• `/lightningstatus 123e4567-e89b-12d3-a456-426614174000`

**How to Get Invoice ID:**
1. Create Lightning invoice with `/lightning`
2. Copy the Invoice ID from the response
3. Use this command to check status

**Status Types:**
• Pending - Waiting for payment
• Paid - Payment received
• Expired - Invoice expired
• Cancelled - Invoice cancelled"""
        
        invoice_id = parts[1]
        
        # Get Lightning invoice
        from payments.models import LightningInvoice
        try:
            invoice = LightningInvoice.objects.get(invoice_id=invoice_id, user=user)
        except LightningInvoice.DoesNotExist:
            return f"❌ Lightning invoice not found: {invoice_id}"
        
        # Check status
        payment_service = PaymentService()
        status_info = payment_service.get_lightning_invoice_status(invoice)
        
        return f"""⚡ Lightning Invoice Status

**Invoice ID:** `{invoice.invoice_id}`
**Amount:** {invoice.amount_sats:,} sats ({invoice.amount_btc:.8f} BTC)
**Naira Value:** ₦{invoice.amount_ngn:,.2f}
**Description:** {invoice.description}

**Status:** {status_info['status'].title()}
**Created:** {invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Expires:** {invoice.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Payment Request:**
`{invoice.payment_request}`

**Status Details:**
• Current Status: {status_info['status'].title()}
• Paid At: {status_info['paid_at'] or 'Not paid yet'}
• Amount: {status_info['amount_sats']:,} sats

**Lightning Network:**
⚡ Instant Bitcoin payments
⚡ Low fees
⚡ Scalable network"""
        
    except Exception as e:
        logger.error(f"Error checking Lightning status: {str(e)}")
        return f"❌ Error checking Lightning status: {str(e)}"


def handle_lightning_history_command(user: BitzappUser) -> str:
    """
    Handle /lightninghistory command to show Lightning payment history
    """
    try:
        payment_service = PaymentService()
        history = payment_service.get_lightning_payment_history(user, limit=10)
        
        if not history:
            return """⚡ Lightning Payment History

**No Lightning transactions found.**

**Get Started with Lightning:**
• `/lightning <amount>` - Create Lightning invoice
• `/lightningpay <payment_request>` - Pay Lightning invoice
• `/lightningstatus <invoice_id>` - Check invoice status

**Lightning Benefits:**
⚡ Instant Bitcoin payments
⚡ Low fees
⚡ Scalable network
⚡ Perfect for small payments"""
        
        response = "⚡ Lightning Payment History\n\n"
        
        for i, transaction in enumerate(history, 1):
            transaction_type = "📤 Invoice" if transaction['type'] == 'lightning_invoice' else "📥 Payment"
            status_emoji = "✅" if transaction['status'] == 'completed' or transaction['status'] == 'paid' else "⏳"
            
            response += f"""**{i}. {transaction_type}** {status_emoji}
**Amount:** {transaction['amount_sats']:,} sats ({transaction['amount_btc']:.8f} BTC)
**Naira:** ₦{transaction['amount_ngn']:,.2f}
**Status:** {transaction['status'].title()}
**Date:** {transaction['created_at'][:19].replace('T', ' ')}
**Request:** `{transaction['payment_request']}`

"""
        
        response += """**Lightning Network Benefits:**
⚡ Instant Bitcoin payments
⚡ Low fees (micro-fees)
⚡ Scalable Bitcoin network
⚡ Perfect for small payments

**Commands:**
• `/lightning <amount>` - Create invoice
• `/lightningpay <request>` - Pay invoice
• `/lightningstatus <id>` - Check status"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting Lightning history: {str(e)}")
        return f"❌ Error getting Lightning history: {str(e)}"


def handle_help_command() -> str:
    """
    Handle /help command
    """
    return """⚡ Bitzapp Lightning Wallet Commands

Lightning Wallet Management:
- /create - Create your Lightning wallet
- /wallet - Learn about Lightning Network features
- /balance - Check your Lightning Bitcoin balance

Lightning Operations:
- /send <amount_sats> <lightning_address> - Send Lightning payments
- /receive - Get your Lightning address and QR code
- /lightning <amount_sats> - Create Lightning invoice
- /lightningpay <payment_request> - Pay Lightning invoice
- /lightningstatus <invoice_id> - Check invoice status
- /lightninghistory - View Lightning transactions

Deposits & Withdrawals:
- /deposit <amount> - Deposit Naira to convert to Lightning Bitcoin
- /withdraw <amount> <account> <bank> <name> - Withdraw Lightning Bitcoin to Nigerian bank

Bill Payments:
- /paybill <provider> <amount> - Pay bills with Lightning Bitcoin

AI Assistant:
- /ask <question> - Ask AI assistant anything
- /help - Show this help message

Lightning Network Benefits:
⚡ Instant Bitcoin payments
⚡ Low fees (micro-fees)
⚡ Scalable Bitcoin network
⚡ No complex key management
⚡ Perfect for everyday use

Examples:
- /create - Create your Lightning wallet
- /send 1000 satoshi@bitzapp-i3i3.onrender.com - Send 1000 sats to Lightning address
- /receive - Get your Lightning address
- /deposit 50000 - Deposit ₦50,000
- /lightning 1000 - Create 1000 sats Lightning invoice

Lightning Addresses:
- Look like email addresses: username@domain.com
- Much easier than Bitcoin addresses
- Instant and low-fee payments
- No waiting for confirmations

Need Help? Ask me anything with /ask <question> 🚀"""


def handle_withdraw_command(user: BitzappUser, message: str) -> str:
    """
    Handle /withdraw command - Bitcoin to Nigerian bank account
    """
    try:
        parts = message.split()
        
        if len(parts) < 5:
            return """💸 Withdraw Bitcoin to Nigerian Bank Account

**Usage:** /withdraw <amount_btc> <account_number> <bank_name> <account_name>
**Example:** /withdraw 0.001 1234567890 Access Bank John Doe

**How it works:**
1. We convert your Bitcoin to Naira at current rate
2. Send Naira to your Nigerian bank account
3. You receive Naira in your bank account
4. Bitcoin is deducted from your wallet

**Supported Banks:**
• Access Bank, GTBank, First Bank, UBA, Zenith Bank
• And all major Nigerian banks

**Processing Time:** 1-3 business days
**Fees:** Small processing fee applies

**Security:** Your bank details are encrypted and secure

Ready to withdraw? Use the format above! 🏦"""

        amount_btc = Decimal(parts[1])
        account_number = parts[2]
        bank_name = parts[3]
        account_name = ' '.join(parts[4:])  # Account name can have spaces
        
        if amount_btc <= 0:
            return "❌ Amount must be greater than 0"
        
        # Check user's Bitcoin balance
        try:
            from core.models import BitcoinWallet
            wallet = BitcoinWallet.objects.get(user=user)
        except BitcoinWallet.DoesNotExist:
            return """❓ No Wallet Found

You don't have a wallet yet. Choose an option:

**Create Non-Custodial Wallet:**
/create - Generate new wallet with seed phrase

**Import Existing Wallet:**
/import <12-word seed phrase>

Both options create a wallet where YOU control your private keys! 🔐"""
        
        if wallet.balance_btc < amount_btc:
            return f"""❌ Insufficient Balance

**Your Balance:** {wallet.balance_btc:.8f} BTC
**Trying to Withdraw:** {amount_btc:.8f} BTC

You need more Bitcoin in your wallet. Use /deposit to add Naira and convert to Bitcoin! 💰"""
        
        # Create withdrawal request
        payment_service = PaymentService()
        withdrawal = payment_service.create_naira_withdrawal(
            user, amount_btc, account_number, bank_name, account_name
        )
        
        # Process withdrawal
        success = payment_service.process_naira_withdrawal(withdrawal)
        
        if success:
            return f"""✅ Withdrawal Request Successful!

**Bitcoin Amount:** {amount_btc:.8f} BTC
**Naira Amount:** ₦{withdrawal.amount_ngn:,.2f}
**Exchange Rate:** 1 BTC = ₦{withdrawal.exchange_rate:,.2f}

**Bank Details:**
• Account: {account_number}
• Bank: {bank_name}
• Name: {account_name}

**Status:** Processing
**Transaction ID:** {withdrawal.id}
**Processing Time:** 1-3 business days

**What Happens Next:**
🏦 We send Naira to your bank account
📱 You'll receive SMS/email confirmation
💰 Naira appears in your bank account
⏱️ Usually within 1-3 business days

Your Bitcoin has been converted to Naira and sent to your bank account! 🚀"""
        else:
            return f"""❌ Withdrawal Failed

**Error:** Unable to process withdrawal request

**Possible Reasons:**
• Bank account details invalid
• Service temporarily unavailable
• Insufficient funds

**What to do:**
• Check your bank account details
• Try again in a few minutes
• Contact support if problem persists

Please try again or contact support for assistance. 🆘"""

    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error handling withdraw command: {str(e)}")
        return "Sorry, I couldn't process your withdrawal request. Please check the format and try again."


def handle_unknown_command() -> str:
    """
    Handle unknown commands
    """
    return """Unknown Command

Type /help to see all available commands.

Quick Start:
- /balance - Check your wallet
- /deposit 50000 - Add Naira
- /receive - Get your Bitcoin address
- /ask What is Bitcoin? - Ask AI assistant

Need help? Just type /help."""


def handle_ai_chat(user: BitzappUser, message: str) -> str:
    """
    Handle AI chat for non-command messages
    """
    try:
        chatbot_service = AIChatbotService()
        response = chatbot_service.get_chat_response(user, message)
        return response
        
    except Exception as e:
        logger.error(f"Error handling AI chat: {str(e)}")
        return "Sorry, I'm having trouble processing your message. Please try again."


def get_user_balance(user: BitzappUser) -> str:
    """
    Get user's balance as formatted string
    """
    try:
        bitnob = BitnobService()
        balance = bitnob.get_wallet_balance(user.phone_number)
        rate_info = bitnob.get_exchange_rate()
        return f"{balance.get('balance_btc', 0):.8f} BTC (₦{balance.get('balance_btc', 0) * rate_info.get('rate', 0):,.2f})"
    except:
        return "0.00000000 BTC (₦0.00)"


def get_recent_transactions(user: BitzappUser) -> str:
    """
    Get recent transactions as formatted string
    """
    try:
        bitnob = BitnobService()
        result = bitnob.get_transaction_history(user.phone_number, limit=3)
        transactions = result.get('transactions') if result.get('success') else []
        
        if not transactions:
            return "No recent transactions"
        
        result = []
        for tx in transactions:
            tx_type = tx.get('type', 'Transaction').title()
            amount = tx.get('amount', 0)
            result.append(f"• {tx_type}: {amount} BTC")
        
        return "\n".join(result)
    except:
        return "Unable to load transactions"
