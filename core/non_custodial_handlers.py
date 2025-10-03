"""
Non-custodial command handlers for Bitzapp
Users control their own private keys through seed phrases
"""
import re
import logging
from decimal import Decimal
from .models import BitzappUser
from wallet.non_custodial_service import NonCustodialWalletService

logger = logging.getLogger('bitzapp')


def handle_create_wallet_command(user: BitzappUser) -> str:
    """
    Create a new non-custodial wallet for user
    """
    try:
        wallet_service = NonCustodialWalletService()
        result = wallet_service.create_wallet_for_user(user)
        
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
        
    except Exception as e:
        logger.error(f"Error creating non-custodial wallet: {str(e)}")
        return "Sorry, I couldn't create your wallet. Please try again."


def handle_import_wallet_command(user: BitzappUser, message: str) -> str:
    """
    Import existing wallet from seed phrase
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
        
        wallet_service = NonCustodialWalletService()
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


def handle_send_with_seed_command(user: BitzappUser, message: str) -> str:
    """
    Send Bitcoin using seed phrase for signing
    """
    try:
        # Extract components from message
        # Format: /send <amount> <address> <seed_phrase>
        parts = message.split()
        if len(parts) < 15:  # /send + amount + address + 12 words
            return """💸 Send Bitcoin (Non-Custodial)

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
        to_address = parts[2]
        seed_phrase = ' '.join(parts[3:15])  # Get 12 words
        
        # Validate amount
        if amount <= 0:
            return "❌ Amount must be greater than 0"
        
        # Create transaction
        wallet_service = NonCustodialWalletService()
        result = wallet_service.create_transaction(user, to_address, amount, seed_phrase)
        
        return f"""✅ Bitcoin Sent Successfully!

**Amount:** {amount:.8f} BTC
**To Address:** {to_address}
**Transaction Hash:** {result['tx_hash']}
**Status:** {result['status']}

**What Happened:**
🔐 You signed the transaction with your private key
🌐 Transaction broadcast to Bitcoin network
💫 Your Bitcoin is being transferred
⏱️ Confirmation in ~10-60 minutes

**Security Note:**
Your seed phrase was used temporarily for signing and then immediately forgotten. We never store your private keys!

Check blockchain explorer with your transaction hash for updates."""
        
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error sending Bitcoin: {str(e)}")
        return "Sorry, I couldn't process your transaction. Please check your details and try again."


def handle_balance_non_custodial_command(user: BitzappUser) -> str:
    """
    Get balance for non-custodial wallet
    """
    try:
        from core.models import BitcoinWallet
        
        try:
            wallet = BitcoinWallet.objects.get(user=user)
            
            # Get live balance from blockchain
            wallet_service = NonCustodialWalletService()
            live_balance = wallet_service.get_balance_from_blockchain(wallet.bitcoin_address)
            
            # Update our cached balance
            wallet.balance_btc = live_balance
            wallet.save()
            
            # Calculate NGN value
            from wallet.services import BitcoinWalletService
            custodial_service = BitcoinWalletService()
            exchange_rate = custodial_service._get_current_exchange_rate()
            balance_ngn = live_balance * exchange_rate
            
            return f"""💰 Your Non-Custodial Wallet Balance

**Bitcoin:** {live_balance:.8f} BTC
**Naira Value:** ₦{balance_ngn:,.2f}
**Exchange Rate:** 1 BTC = ₦{exchange_rate:,.2f}

**Your Bitcoin Address:**
`{wallet.bitcoin_address}`

**Wallet Type:** 🔐 Non-Custodial
✅ You control your private keys
✅ Decentralized and secure
✅ No single point of failure

**Security Status:**
🔐 Your seed phrase is safe with you
🔐 We never store your private keys
🔐 Only you can access your Bitcoin

To send Bitcoin, use: /send <amount> <address> <seed_phrase>"""
            
        except BitcoinWallet.DoesNotExist:
            return """❓ No Wallet Found

You don't have a wallet yet. Choose an option:

**Create New Wallet:**
/create - Generate new wallet with seed phrase

**Import Existing Wallet:**
/import <12-word seed phrase>

Both options create a non-custodial wallet where YOU control your private keys! 🔐"""
        
    except Exception as e:
        logger.error(f"Error getting non-custodial balance: {str(e)}")
        return "Sorry, I couldn't retrieve your balance. Please try again."


def handle_wallet_info_command() -> str:
    """
    Explain non-custodial wallet concept
    """
    return """🔐 Non-Custodial Wallet Information

**What is Non-Custodial?**
• YOU control your private keys
• WE cannot access your Bitcoin
• Your Bitcoin is truly yours
• No central authority can freeze your funds

**How It Works:**
1. You get a 12-word seed phrase
2. This generates your private keys
3. You store the seed phrase safely
4. You provide it for transactions

**Security Benefits:**
✅ Decentralized - no single point of failure
✅ Private - only you control your Bitcoin
✅ Secure - we can't be hacked for your funds
✅ Transparent - all transactions on blockchain

**Your Responsibilities:**
🔐 Keep your seed phrase safe
🔐 Never share it with anyone
🔐 Back it up securely
🔐 Remember: if you lose it, Bitcoin is gone

**Why Choose Non-Custodial?**
This is the true spirit of Bitcoin - be your own bank!

Ready to create your non-custodial wallet? Type /create"""


def get_non_custodial_help() -> str:
    """
    Help message for non-custodial features
    """
    return """🔐 Non-Custodial Bitzapp Commands

**Wallet Management:**
• /create - Create new non-custodial wallet
• /import <seed phrase> - Import existing wallet
• /balance - Check your Bitcoin balance
• /info - Learn about non-custodial wallets

**Transactions:**
• /send <amount> <address> <seed phrase> - Send Bitcoin
• /receive - Get your Bitcoin address

**Security Features:**
🔐 You control your private keys
🔐 We never store your seed phrase
🔐 Truly decentralized Bitcoin wallet
🔐 No single point of failure

**Important Notes:**
⚠️ Keep your seed phrase safe - we cannot recover it
⚠️ Never share your seed phrase with anyone
⚠️ Back up your seed phrase securely
⚠️ If you lose it, your Bitcoin is gone forever

**Why Non-Custodial?**
This is Bitcoin as it was meant to be - you are your own bank!

Need help? Ask our AI: /ask What is a seed phrase?"""
