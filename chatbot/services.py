"""
AI Chatbot service for Bitzapp
Handles conversations with users about Bitcoin and Bitzapp features
"""
import requests
import logging
import time
from django.conf import settings
from core.models import BitzappUser
from chatbot.models import ChatSession, ChatMessage, AIKnowledge

logger = logging.getLogger('bitzapp')


class AIChatbotService:
    """
    Service for AI chatbot interactions
    """
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.gemini_base_url = 'https://generativelanguage.googleapis.com/v1beta'
    
    def start_chat_session(self, user: BitzappUser) -> ChatSession:
        """
        Start a new chat session for a user
        """
        try:
            # Deactivate existing sessions
            ChatSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Create new session
            session = ChatSession.objects.create(
                user=user,
                is_active=True
            )
            
            # Add welcome message
            welcome_message = self._get_welcome_message()
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=welcome_message,
                tokens_used=0
            )
            
            logger.info(f"Started chat session for user {user.phone_number}")
            return session
            
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            raise
    
    def _get_welcome_message(self) -> str:
        """
        Get welcome message for new chat sessions
        """
        return """🚀 Welcome to Bitzapp - Your Bitcoin Wallet in WhatsApp!

I'm your AI assistant here to help you with Bitcoin and Bitzapp features.

**To Get Started:**
Type `/create` to create your Bitcoin wallet and begin your journey!

**What I can help you with:**
• Bitcoin basics and education
• Creating and managing your wallet
• Sending and receiving Bitcoin
• Paying bills with Bitcoin
• Security tips and best practices

**Quick Commands:**
• `/create` - Create your Bitcoin wallet
• `/help` - See all available commands
• `/balance` - Check your Bitcoin balance

Just ask me anything about Bitcoin or Bitzapp! 

Ready to start? Type `/create` to create your wallet! 🚀"""
    
    def get_chat_response(self, user: BitzappUser, message: str) -> str:
        """
        Get AI response to user message
        """
        try:
            start_time = time.time()
            
            # Get or create active session
            session = self._get_active_session(user)
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=message
            )
            
            # Check if it's a command
            if message.startswith('/'):
                response = self._handle_command(user, message)
            else:
                # Generate AI response
                response = self._generate_ai_response(user, message, session)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Save AI response
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=response,
                tokens_used=len(response.split()),  # Approximate token count
                response_time=response_time
            )
            
            logger.info(f"Generated AI response for user {user.phone_number}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "Sorry, I'm having trouble processing your request. Please try again later."
    
    def _get_active_session(self, user: BitzappUser) -> ChatSession:
        """
        Get or create active chat session
        """
        try:
            session = ChatSession.objects.filter(
                user=user,
                is_active=True
            ).first()
            
            if not session:
                session = self.start_chat_session(user)
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting active session: {str(e)}")
            raise
    
    def _handle_command(self, user: BitzappUser, command: str) -> str:
        """
        Handle special commands
        """
        command = command.lower().strip()
        
        if command == '/help':
            return self._get_help_message()
        elif command == '/balance':
            return self._get_balance_info(user)
        elif command == '/commands':
            return self._get_commands_list()
        elif command == '/bitcoin':
            return self._get_bitcoin_info()
        elif command == '/security':
            return self._get_security_tips()
        else:
            return "Unknown command. Type /help to see available commands."
    
    def _get_help_message(self) -> str:
        """
        Get help message with available commands
        """
        return """🤖 Bitzapp AI Assistant Help

**Available Commands:**
• /help - Show this help message
• /balance - Check your Bitcoin wallet balance
• /commands - List all available commands
• /bitcoin - Learn about Bitcoin basics
• /security - Get security tips

**Bitzapp Features:**
• Send Bitcoin: /send <amount> <address>
• Receive Bitcoin: /receive
• Pay bills: /paybill <provider> <amount>
• Deposit Naira: /deposit <amount>

**Ask me anything about:**
• Bitcoin and cryptocurrency
• Bitzapp features and usage
• Security and best practices
• Troubleshooting issues

Just type your question and I'll help you! 🚀"""
    
    def _get_balance_info(self, user: BitzappUser) -> str:
        """
        Get user's balance information
        """
        try:
            from wallet.services import BitcoinWalletService
            wallet_service = BitcoinWalletService()
            balance = wallet_service.get_wallet_balance(user)
            
            return f"""💰 Your Bitcoin Wallet Balance

**Bitcoin:** {balance['balance_btc']:.8f} BTC
**Naira:** ₦{balance['balance_ngn']:,.2f}
**Exchange Rate:** 1 BTC = ₦{balance['exchange_rate']:,.2f}

**Your Bitcoin Address:**
`{balance['bitcoin_address']}`

Use this address to receive Bitcoin from others! 🚀"""
            
        except Exception as e:
            logger.error(f"Error getting balance info: {str(e)}")
            return "Sorry, I couldn't retrieve your balance. Please try again later."
    
    def _get_commands_list(self) -> str:
        """
        Get list of available commands
        """
        return """📋 Available Commands

**Wallet Commands:**
• /balance - Check your Bitcoin balance
• /send <amount> <address> - Send Bitcoin
• /receive - Get your Bitcoin address

**Payment Commands:**
• /deposit <amount> - Deposit Naira
• /paybill <provider> <amount> - Pay bills

**Information Commands:**
• /help - Show help message
• /bitcoin - Bitcoin basics
• /security - Security tips
• /commands - This command list

**AI Assistant:**
Just ask me anything about Bitcoin or Bitzapp! 🤖"""
    
    def _get_bitcoin_info(self) -> str:
        """
        Get Bitcoin basics information
        """
        return """₿ Bitcoin Basics

**What is Bitcoin?**
Bitcoin is a decentralized digital currency that allows peer-to-peer transactions without intermediaries like banks.

**Key Features:**
• Decentralized - No central authority
• Secure - Cryptographically protected
• Transparent - All transactions are public
• Limited Supply - Only 21 million Bitcoin will ever exist

**How Bitcoin Works:**
1. Transactions are recorded on a public ledger (blockchain)
2. Miners verify and secure transactions
3. You control your Bitcoin with private keys
4. No one can freeze or confiscate your Bitcoin

**Bitcoin in Nigeria:**
• Store of value against inflation
• Fast international transfers
• Lower fees than traditional banking
• Financial freedom and control

**Security Tips:**
• Never share your private keys
• Use hardware wallets for large amounts
• Verify addresses before sending
• Keep your seed phrase safe

Want to learn more? Just ask! 🚀"""
    
    def _get_security_tips(self) -> str:
        """
        Get security tips for Bitcoin users
        """
        return """🔒 Bitcoin Security Tips

**Protect Your Private Keys:**
• Never share your private keys or seed phrase
• Store them offline and secure
• Use hardware wallets for large amounts
• Don't store keys on your phone or computer

**Safe Practices:**
• Always verify addresses before sending
• Use small amounts for testing
• Keep your Bitcoin in multiple wallets
• Regularly update your wallet software

**Avoid Scams:**
• Never send Bitcoin to "recover" your account
• Be wary of "free Bitcoin" offers
• Don't trust random links or messages
• Verify information from official sources

**Bitzapp Security:**
• Your Bitcoin is stored securely
• We never have access to your private keys
• All transactions are encrypted
• We use industry-standard security practices

**If You're Compromised:**
• Immediately transfer your Bitcoin to a new wallet
• Change all passwords
• Report the incident
• Learn from the experience

Stay safe and secure! 🛡️"""
    
    def _generate_ai_response(self, user: BitzappUser, message: str, session: ChatSession) -> str:
        """
        Generate AI response using Gemini API
        """
        try:
            # Check if it's a greeting first
            greeting_response = self._handle_greeting(message, user)
            if greeting_response:
                return greeting_response
            
            if not self.gemini_api_key:
                return self._get_fallback_response(message)
            
            # Get conversation history
            conversation_history = self._get_conversation_history(session)
            
            # Prepare prompt
            prompt = self._build_prompt(message, conversation_history)
            
            # Call Gemini API
            response = self._call_gemini_api(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(message)
    
    def _get_conversation_history(self, session: ChatSession, limit: int = 10) -> list:
        """
        Get conversation history for context
        """
        try:
            messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-created_at')[:limit]
            
            history = []
            for message in reversed(messages):
                role = "user" if message.message_type == "user" else "assistant"
                history.append({
                    "role": role,
                    "content": message.content
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
    
    def _build_prompt(self, message: str, history: list) -> str:
        """
        Build prompt for Gemini API
        """
        system_prompt = """You are Bitzapp AI Assistant, a helpful AI that specializes in Bitcoin and the Bitzapp WhatsApp Bitcoin wallet.

Your role:
- Help users understand Bitcoin and cryptocurrency
- Explain Bitzapp features and commands
- Provide security tips and best practices
- Troubleshoot user issues
- Guide new users to create their wallet with /create command
- Be friendly, helpful, and educational

Context about Bitzapp:
- It's a Bitcoin wallet inside WhatsApp
- Users can send/receive Bitcoin via WhatsApp
- Users can deposit Naira and convert to Bitcoin
- Users can pay bills using Bitcoin
- It's designed for Nigerian users
- New users should type /create to create their wallet

Important: If a user seems new or confused, always guide them to type /create to get started with their Bitcoin wallet.

Keep responses concise, helpful, and focused on Bitcoin/Bitzapp topics."""
        
        # Build conversation context
        context = system_prompt + "\n\nConversation:\n"
        for msg in history:
            context += f"{msg['role']}: {msg['content']}\n"
        
        context += f"user: {message}\nassistant:"
        
        return context
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Call Gemini API for AI response
        """
        try:
            url = f"{self.gemini_base_url}/models/gemini-pro:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            params = {
                'key': self.gemini_api_key
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
                else:
                    logger.error("No candidates in Gemini response")
                    return self._get_fallback_response("")
            else:
                logger.error(f"Gemini API error: {response.status_code}")
                return self._get_fallback_response("")
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return self._get_fallback_response("")
    
    def _handle_greeting(self, message: str, user: BitzappUser) -> str:
        """
        Handle greeting messages and guide users to create wallet
        """
        try:
            message_lower = message.lower().strip()
            
            # Common greeting patterns
            greetings = [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                'hi bitzapp', 'hello bitzapp', 'hey bitzapp', 'hi there', 'hello there',
                'start', 'begin', 'get started', 'new user', 'first time'
            ]
            
            # Check if message contains greeting
            is_greeting = any(greeting in message_lower for greeting in greetings)
            
            if is_greeting:
                # Check if user has a wallet
                from core.models import BitcoinWallet
                try:
                    wallet = BitcoinWallet.objects.get(user=user)
                    # User has wallet, provide helpful response
                    return f"""👋 Hello! Great to see you again!

I see you already have a Bitcoin wallet set up. How can I help you today?

**Quick Actions:**
• `/balance` - Check your Bitcoin balance
• `/send` - Send Bitcoin to someone
• `/receive` - Get your Bitcoin address
• `/deposit` - Add Naira to convert to Bitcoin
• `/help` - See all commands

**Ask me anything about:**
• Bitcoin and cryptocurrency
• Using your wallet
• Security tips
• Bitzapp features

What would you like to do? 🚀"""
                except BitcoinWallet.DoesNotExist:
                    # User doesn't have wallet, guide them to create one
                    return f"""👋 Hello! Welcome to Bitzapp! 

I'm excited to help you get started with Bitcoin! 

**To begin your Bitcoin journey:**
Type `/create` to create your Bitcoin wallet and start using Bitcoin right here in WhatsApp!

**What you'll get:**
🔐 Your own Bitcoin wallet
💰 Ability to send and receive Bitcoin
💳 Pay bills with Bitcoin
🏦 Convert Naira to Bitcoin
⚡ Lightning-fast payments

**Ready to start?**
Type `/create` to create your wallet now! 🚀

**Need help?** Just ask me anything about Bitcoin!"""
            
            return None  # Not a greeting, continue with normal AI processing
            
        except Exception as e:
            logger.error(f"Error handling greeting: {str(e)}")
            return None
    
    def _get_fallback_response(self, message: str) -> str:
        """
        Get fallback response when AI is unavailable
        """
        # Check if message contains Bitcoin-related keywords
        bitcoin_keywords = ['bitcoin', 'btc', 'crypto', 'wallet', 'blockchain']
        if any(keyword in message.lower() for keyword in bitcoin_keywords):
            return """I'm having trouble connecting to my AI brain right now, but I can still help with Bitcoin basics!

**Bitcoin Quick Facts:**
• Bitcoin is digital money that works without banks
• It's secure, fast, and global
• You can send it to anyone, anywhere
• It's a great store of value

**Get Started with Bitzapp:**
• `/create` - Create your Bitcoin wallet
• `/balance` - Check your balance
• `/send` - Send Bitcoin
• `/receive` - Get your address
• `/deposit` - Add Naira to convert to Bitcoin

**Ready to start?** Type `/create` to create your wallet! 🚀"""
        
        return """I'm having some technical difficulties right now, but I'm here to help!

**Quick Start Guide:**
• Type `/create` to create your Bitcoin wallet
• Type `/help` for available commands
• Type `/balance` to check your wallet
• Type `/bitcoin` for Bitcoin basics
• Type `/security` for safety tips

**New to Bitcoin?** Type `/create` to get started! 🚀"""
    
    def get_chat_history(self, user: BitzappUser, limit: int = 20) -> list:
        """
        Get user's chat history
        """
        try:
            session = self._get_active_session(user)
            messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'type': msg.message_type,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []
