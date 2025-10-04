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
from chatbot.services import AIChatbotService

logger = logging.getLogger('bitzapp')


def handle_create_wallet_command(user: BitzappUser) -> str:
    """
    Handle /create command for non-custodial wallet
    """
    try:
        wallet_service = BitcoinWalletService()
        result = wallet_service._create_non_custodial_wallet(user)
        
        if result['seed_phrase'] == 'EXISTING_WALLET':
            return f"""🔐 Non-Custodial Wallet Already Exists!

**Your Bitcoin Address:**
`{result['bitcoin_address']}`

**Wallet Status:** ✅ Active Non-Custodial Wallet

**Security Reminder:**
🔐 You already control your private keys
🔐 We never store your seed phrase
🔐 Your wallet is truly decentralized

**Commands:**
• /balance - Check your balance
• /send - Send Bitcoin (requires seed phrase)
• /receive - Get your Bitcoin address

Your non-custodial wallet is ready to use! 🚀"""
        
        return f"""🔐 Non-Custodial Wallet Created!

**⚠️ CRITICAL WARNING: SAVE THIS SEED PHRASE SAFELY! ⚠️**

**Your 12-Word Seed Phrase:**
`{result['seed_phrase']}`

**Your Bitcoin Address:**
`{result['bitcoin_address']}`

**IMPORTANT SECURITY NOTES:**
🚨 We DO NOT store your seed phrase
🚨 If you lose it, your Bitcoin is GONE FOREVER
🚨 Never share your seed phrase with anyone
🚨 Write it down on paper and store safely
🚨 Take a photo and store in encrypted backup

**Why Non-Custodial?**
✅ You control your private keys
✅ We cannot access your Bitcoin
✅ Decentralized and secure
✅ No single point of failure

To use your wallet, you'll need to provide your seed phrase for transactions.

Type /import to import an existing wallet or /help for commands."""
        
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.error(f"Error creating non-custodial wallet: {str(e)}")
        return "Sorry, I couldn't create your wallet. Please try again."


def handle_import_wallet_command(user: BitzappUser, message: str) -> str:
    """
    Handle /import command for existing wallet
    """
    try:
        # Extract seed phrase from message
        # Format: /import word1 word2 word3 ... word12
        parts = message.split()
        if len(parts) < 13:  # /import + 12 words
            return """🔐 Import Existing Wallet

**Usage:** /import <12-word seed phrase>
**Example:** /import abandon ability able about above absent absorb abstract absurd abuse access accident

**Security Tips:**
• Only import your own seed phrase
• Make sure you're in a private chat
• Delete the message after importing
• Never share your seed phrase

This will import your existing Bitcoin wallet into Bitzapp."""
        
        seed_phrase = ' '.join(parts[1:13])  # Get 12 words
        
        wallet_service = BitcoinWalletService()
        result = wallet_service.import_wallet_from_seed(user, seed_phrase)
        
        return f"""✅ Wallet Imported Successfully!

**Your Bitcoin Address:**
`{result['bitcoin_address']}`

**Current Balance:** {result['balance']:.8f} BTC

**Security Reminder:**
🔐 Your seed phrase is safe with you
🔐 We never store your private keys
🔐 Delete the message containing your seed phrase

Your non-custodial wallet is now active! Use /balance to check your funds."""
        
    except ValueError as e:
        return f"❌ Invalid seed phrase: {str(e)}"
    except Exception as e:
        logger.error(f"Error importing wallet: {str(e)}")
        return "Sorry, I couldn't import your wallet. Please check your seed phrase and try again."


def handle_wallet_info_command() -> str:
    """
    Handle /wallet command to explain wallet types
    """
    return """🔐 Wallet Types Explained

**Custodial Wallet (Easy Mode):**
• We manage your private keys
• Easy to use, no seed phrases
• Good for beginners
• Small amounts

**Non-Custodial Wallet (Secure Mode):**
• YOU control your private keys
• Requires seed phrase management
• Maximum security
• True decentralization

**Commands:**
• /create - Create non-custodial wallet
• /import <seed phrase> - Import existing wallet
• /balance - Check your balance
• /send - Send Bitcoin (requires seed phrase for non-custodial)

**Choose Your Security Level:**
🔐 Non-custodial = Maximum security, you control everything
🏦 Custodial = Easy to use, we help manage your keys

Ready to create your wallet? Type /create for non-custodial!"""


def handle_deposit_command(user: BitzappUser, message: str) -> str:
    """
    Handle /save or /deposit command
    """
    try:
        # Extract amount from message
        amount_match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not amount_match:
            return """💰 Deposit Naira to Convert to Bitcoin

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
        
        # Create deposit request
        payment_service = PaymentService()
        deposit = payment_service.create_naira_deposit(user, amount)
        
        return f"""💰 Deposit Request Created

**Amount:** ₦{amount:,.2f}
**Bitcoin Equivalent:** {deposit.amount_btc:.8f} BTC
**Exchange Rate:** 1 BTC = ₦{deposit.exchange_rate:,.2f}

**Next Steps:**
1. Send ₦{amount:,.2f} to our bank account
2. Include reference: DEP{user.id}
3. We'll process within 24 hours

**Bank Details:**
Account: Bitzapp Limited
Account Number: 1234567890
Bank: Access Bank

Your Bitcoin will be added to your wallet once payment is confirmed! 🚀"""
        
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
            return """❓ No Wallet Found

You don't have a wallet yet. Choose an option:

**Create Non-Custodial Wallet:**
/create - Generate new wallet with seed phrase

**Import Existing Wallet:**
/import <12-word seed phrase>

Both options create a wallet where YOU control your private keys! 🔐"""
        
        wallet_service = BitcoinWalletService()
        balance = wallet_service.get_wallet_balance(user)
        
        wallet_type = "🔐 Non-Custodial" if wallet.is_non_custodial else "🏦 Custodial"
        security_status = "You control your private keys" if wallet.is_non_custodial else "We manage your private keys"
        
        return f"""💰 Your Bitcoin Wallet Balance

**Bitcoin:** {balance['balance_btc']:.8f} BTC
**Naira Value:** ₦{balance['balance_ngn']:,.2f}
**Exchange Rate:** 1 BTC = ₦{balance['exchange_rate']:,.2f}

**Your Bitcoin Address:**
`{balance['bitcoin_address']}`

**Wallet Type:** {wallet_type}
**Security:** {security_status}

**Recent Transactions:**
{get_recent_transactions(user)}

**Commands:**
• /send - Send Bitcoin {'(requires seed phrase)' if wallet.is_non_custodial else ''}
• /receive - Get your Bitcoin address
• /deposit - Add Naira to convert to Bitcoin

Use your Bitcoin address to receive Bitcoin from others! 🚀"""
        
    except Exception as e:
        logger.error(f"Error handling balance command: {str(e)}")
        return "Sorry, I couldn't retrieve your balance. Please try again."


def handle_send_command(user: BitzappUser, message: str) -> str:
    """
    Handle /send command - supports both custodial and non-custodial wallets
    """
    try:
        from .models import BitcoinWallet
        
        # Check if user has a wallet
        try:
            wallet = BitcoinWallet.objects.get(user=user)
        except BitcoinWallet.DoesNotExist:
            return """❓ No Wallet Found

You don't have a wallet yet. Choose an option:

**Create Non-Custodial Wallet:**
/create - Generate new wallet with seed phrase

**Import Existing Wallet:**
/import <12-word seed phrase>

Both options create a wallet where YOU control your private keys! 🔐"""
        
        # Extract components from message
        parts = message.split()
        
        if wallet.is_custodial:
            # Custodial wallet - simple format
            if len(parts) < 3:
                return """💸 Send Bitcoin (Custodial Wallet)

**Usage:** /send <amount> <address>
**Example:** /send 0.001 bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

**Current Balance:** {get_user_balance(user)}

**How to send:**
1. Get recipient's Bitcoin address
2. Use the format above
3. Confirm the transaction
4. Bitcoin will be sent instantly

**Security Tips:**
• Always verify the address before sending
• Start with small amounts for new addresses
• Double-check the amount

Ready to send Bitcoin? Use the format above! 🚀"""
            
            amount = Decimal(parts[1])
            address = parts[2]
            seed_phrase = None
            
        elif wallet.is_non_custodial:
            # Non-custodial wallet - requires seed phrase
            if len(parts) < 15:  # /send + amount + address + 12 words
                return """💸 Send Bitcoin (Non-Custodial Wallet)

**Usage:** /send <amount> <address> <12-word seed phrase>
**Example:** /send 0.001 bc1qxy2k... abandon ability able about above absent absorb abstract absurd abuse access accident

**Security Process:**
1. We use your seed phrase to sign the transaction
2. We immediately forget your seed phrase
3. Transaction is broadcast to Bitcoin network
4. Your Bitcoin is sent directly from your wallet

**Security Tips:**
• Only send to verified addresses
• Start with small amounts for new addresses
• Delete your message after sending
• Never share your seed phrase with others

This is a truly decentralized transaction - you control everything!"""
            
            amount = Decimal(parts[1])
            address = parts[2]
            seed_phrase = ' '.join(parts[3:15])  # Get 12 words
        
        # Validate amount
        if amount <= 0:
            return "❌ Amount must be greater than 0"
        
        # Check balance
        wallet_service = BitcoinWalletService()
        balance = wallet_service.get_wallet_balance(user)
        
        if balance['balance_btc'] < amount:
            return f"""❌ Insufficient Balance

**Your Balance:** {balance['balance_btc']:.8f} BTC
**Trying to Send:** {amount:.8f} BTC

You need more Bitcoin in your wallet. Use /deposit to add Naira and convert to Bitcoin! 💰"""
        
        # Send Bitcoin
        transaction_obj = wallet_service.send_bitcoin(
            user, address, amount, f"Sent {amount} BTC to {address}", seed_phrase
        )
        
        wallet_type = "Non-Custodial" if wallet.is_non_custodial else "Custodial"
        
        return f"""✅ Bitcoin Sent Successfully!

**Amount:** {amount:.8f} BTC
**To Address:** {address}
**Transaction ID:** {transaction_obj.id}
**Naira Value:** ₦{float(amount) * balance['exchange_rate']:,.2f}
**Wallet Type:** {wallet_type}

**What Happened:**
{'🔐 You signed the transaction with your private key' if wallet.is_non_custodial else '🏦 We processed the transaction for you'}
🌐 Transaction broadcast to Bitcoin network
💫 Your Bitcoin is being transferred
⏱️ Confirmation in ~10-60 minutes

{'**Security Note:** Your seed phrase was used temporarily for signing and then immediately forgotten. We never store your private keys!' if wallet.is_non_custodial else '**Security Note:** Your transaction was processed securely through our custodial system.'}

Check blockchain explorer with your transaction hash for updates."""
        
    except Exception as e:
        logger.error(f"Error handling send command: {str(e)}")
        return "Sorry, I couldn't process your send request. Please check the format and try again."


def handle_receive_command(user: BitzappUser) -> str:
    """
    Handle /receive command
    """
    try:
        wallet_service = BitcoinWalletService()
        balance = wallet_service.get_wallet_balance(user)
        
        return f"""📥 Receive Bitcoin

**Your Bitcoin Address:**
`{balance['bitcoin_address']}`

**How to receive Bitcoin:**
1. Share this address with the sender
2. They send Bitcoin to this address
3. You'll receive it in your wallet
4. Check balance with /balance

**Current Balance:** {balance['balance_btc']:.8f} BTC (₦{balance['balance_ngn']:,.2f})

**Security Tips:**
• This address is unique to you
• You can use it multiple times
• Always verify the address before sharing
• Never share your private keys

Share this address to receive Bitcoin! 🚀"""
        
    except Exception as e:
        logger.error(f"Error handling receive command: {str(e)}")
        return "Sorry, I couldn't retrieve your Bitcoin address. Please try again."


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
        
        # Create Lightning invoice
        payment_service = PaymentService()
        invoice = payment_service.create_lightning_invoice(user, amount_sats, description)
        
        return f"""⚡ Lightning Invoice Created!

**Amount:** {amount_sats:,} sats ({invoice.amount_btc:.8f} BTC)
**Naira Value:** ₦{invoice.amount_ngn:,.2f}
**Description:** {description}

**Payment Request:**
`{invoice.payment_request}`

**Invoice Details:**
• Invoice ID: `{invoice.invoice_id}`
• Expires: {invoice.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC
• Status: {invoice.status.title()}

**How to Pay:**
1. Copy the payment request above
2. Use any Lightning wallet (Phoenix, Breez, etc.)
3. Scan or paste the payment request
4. Confirm the payment

**Lightning Benefits:**
⚡ Instant confirmation
⚡ Micro-fee payments
⚡ Scalable Bitcoin network

Your Lightning invoice is ready! 🚀"""
        
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
        
        # Pay Lightning invoice
        payment_service = PaymentService()
        payment = payment_service.pay_lightning_invoice(user, payment_request, description)
        
        return f"""⚡ Lightning Payment Successful!

**Amount:** {payment.amount_sats:,} sats ({payment.amount_btc:.8f} BTC)
**Naira Value:** ₦{payment.amount_ngn:,.2f}
**Description:** {description}

**Payment Details:**
• Payment ID: `{payment.payment_id}`
• Status: {payment.status.title()}
• Completed: {payment.completed_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Transaction Hash:**
`{payment.payment_hash}`

**Lightning Benefits:**
⚡ Instant confirmation
⚡ Micro-fee payment
⚡ Scalable Bitcoin network

Your Lightning payment is complete! 🚀"""
        
    except ValueError as e:
        if "Insufficient Bitcoin balance" in str(e):
            return f"""❌ Insufficient Bitcoin Balance

You don't have enough Bitcoin to complete this Lightning payment.

**Your Balance:** Check with `/balance`
**Required:** {payment.amount_btc:.8f} BTC

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
    return """🤖 Bitzapp Bitcoin Wallet Commands

**🔐 Wallet Management:**
• /create - Create non-custodial wallet (you control keys)
• /import <seed phrase> - Import existing wallet
• /wallet - Learn about wallet types
• /balance - Check your Bitcoin balance

**⚡ Lightning Network:**
• /lightning <amount_sats> - Create Lightning invoice
• /lightningpay <payment_request> - Pay Lightning invoice
• /lightningstatus <invoice_id> - Check invoice status
• /lightninghistory - View Lightning transactions

**💰 Bitcoin Operations:**
• /send <amount> <address> - Send Bitcoin (custodial)
• /send <amount> <address> <seed phrase> - Send Bitcoin (non-custodial)
• /receive - Get your Bitcoin address
• /deposit <amount> - Deposit Naira to convert to Bitcoin
• /withdraw <amount> <account> <bank> <name> - Withdraw Bitcoin to Nigerian bank

**💳 Bill Payments:**
• /paybill <provider> <amount> - Pay bills with Bitcoin

**🤖 AI Assistant:**
• /ask <question> - Ask AI assistant anything
• /help - Show this help message

**⚡ Lightning Benefits:**
• Instant Bitcoin payments
• Low fees (micro-fees)
• Scalable Bitcoin network
• Perfect for small payments

**Wallet Types:**
🔐 **Non-Custodial** - You control your private keys (maximum security)
🏦 **Custodial** - We manage your private keys (easy to use)

**Examples:**
• /create - Create new non-custodial wallet
• /lightning 1000 - Create 1000 sats Lightning invoice
• /lightningpay lnbc1000u1p... - Pay Lightning invoice
• /deposit 50000 - Deposit ₦50,000
• /paybill mtn 1000 08012345678 - Pay MTN airtime

**Security Reminder:**
🔐 Save your seed phrase safely!
🔐 Never share your private keys
🔐 Use Lightning for instant payments

**Need Help?** Ask me anything with /ask <question>"""


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
    return """❓ Unknown Command

Type /help to see all available commands.

**Quick Start:**
• /balance - Check your wallet
• /deposit 50000 - Add Naira
• /receive - Get your Bitcoin address
• /ask What is Bitcoin? - Ask AI assistant

Need help? Just type /help! 🚀"""


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
        wallet_service = BitcoinWalletService()
        balance = wallet_service.get_wallet_balance(user)
        return f"{balance['balance_btc']:.8f} BTC (₦{balance['balance_ngn']:,.2f})"
    except:
        return "0.00000000 BTC (₦0.00)"


def get_recent_transactions(user: BitzappUser) -> str:
    """
    Get recent transactions as formatted string
    """
    try:
        wallet_service = BitcoinWalletService()
        transactions = wallet_service.get_transaction_history(user, limit=3)
        
        if not transactions:
            return "No recent transactions"
        
        result = []
        for tx in transactions:
            result.append(f"• {tx['type'].title()}: {tx['amount_btc']:.8f} BTC")
        
        return "\n".join(result)
    except:
        return "Unable to load transactions"
