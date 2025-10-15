"""
AI Intent Classification Service for Bitzapp
Classifies user messages into financial intents or conversational chat
Uses hybrid approach: regex for simple commands, Gemini for complex natural language
"""
import json
import re
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('bitzapp')


class IntentClassifier:
    """
    Classifies user messages into intents for the Bitcoin wallet
    """
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.gemini_base_url = 'https://generativelanguage.googleapis.com/v1beta'
        self.intent_patterns = {
            'create_wallet': [
                r'\b(?:create|open|make|new)\s+(?:wallet|btc|bitcoin)\b',
                r'\b(?:wallet|btc|bitcoin)\s+(?:create|open|make|new)\b',
                r'^/create$',
                r'\b(?:i\s+)?(?:need|want)\s+(?:a\s+)?(?:wallet|btc|bitcoin)\b',
                r'\b(?:get|start)\s+(?:wallet|btc|bitcoin)\b'
            ],
            'deposit': [
                r'\b(?:deposit|buy|add|convert|save)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\b',
                r'\b(?:₦|naira|ngn)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:to\s+)?(?:bitcoin|btc)\b',
                r'\b(?:bitcoin|btc)\s+(?:with|for)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\b',
                r'^/deposit\s+(\d+(?:,\d{3})*(?:\.\d+)?)',
                r'\b(?:i\s+)?(?:want|need)\s+(?:to\s+)?(?:deposit|buy|add)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\b'
            ],
            'send': [
                r'\b(?:send|transfer|give)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\s*(?:worth\s+of\s+)?(?:btc|bitcoin)\s+(?:to|for)\s+([a-zA-Z0-9\s]+)',
                r'\b(?:send|transfer|give)\s+(\d+(?:\.\d+)?)\s*(?:btc|bitcoin)\s+(?:to|for)\s+([a-zA-Z0-9\s]+)',
                r'^/send\s+(\d+(?:\.\d+)?)\s+([a-zA-Z0-9\s]+)',
                r'\b(?:send|transfer|give)\s+(?:to|for)\s+([a-zA-Z0-9\s]+)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\b'
            ],
            'balance': [
                r'\b(?:balance|check|show|what\s+is)\s+(?:my\s+)?(?:balance|wallet|btc|bitcoin)\b',
                r'\b(?:how\s+much|how\s+many)\s+(?:btc|bitcoin)\s+(?:do\s+i\s+)?(?:have|own)\b',
                r'^/balance$',
                r'\b(?:my\s+)?(?:balance|wallet|btc|bitcoin)\s+(?:balance|amount|value)\b'
            ],
            'withdraw': [
                r'\b(?:withdraw|cash\s+out|convert\s+to\s+naira)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\s*(?:to\s+)?(?:my\s+)?(?:bank|account)\b',
                r'\b(?:send|transfer)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\s*(?:to\s+)?(?:my\s+)?(?:bank|account)\b',
                r'^/withdraw\s+(\d+(?:,\d{3})*(?:\.\d+)?)',
                r'\b(?:i\s+)?(?:want|need)\s+(?:to\s+)?(?:withdraw|cash\s+out)\s+(?:₦|naira|ngn)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|₦)?\b'
            ],
            'transactions': [
                r'\b(?:transactions|history|activity|statement|record)\b',
                r'\b(?:show|see|view|get)\s+(?:my\s+)?(?:transactions|history|activity)\b',
                r'^/history$',
                r'\b(?:what\s+did\s+i\s+)?(?:spend|send|receive)\b'
            ],
            'receive': [
                r'\b(?:receive|get|my\s+address|bitcoin\s+address)\b',
                r'^/receive$',
                r'\b(?:how\s+to\s+)?(?:receive|get)\s+(?:bitcoin|btc)\b',
                r'\b(?:my\s+)?(?:address|wallet\s+address)\b'
            ]
        }
    
    def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify user message into intent and extract parameters using hybrid approach
        """
        try:
            message_lower = message.lower().strip()
            
            # Step 1: Check for simple slash commands first (regex)
            if message.startswith('/'):
                return self._handle_slash_command(message)
            
            # Step 2: Check for obvious financial intents with regex (fast)
            regex_result = self._classify_with_regex(message_lower)
            if regex_result["intent"] != "chat":
                return regex_result
            
            # Step 3: Use Gemini for complex natural language understanding
            if self.gemini_api_key:
                gemini_result = self._classify_with_gemini(message)
                if gemini_result["intent"] != "chat":
                    return gemini_result
            
            # Step 4: Fallback to chat
            return {"intent": "chat", "message": message}
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return {"intent": "chat", "message": message}
    
    def _classify_with_regex(self, message_lower: str) -> Dict[str, Any]:
        """
        Classify intent using regex patterns (fast method)
        """
        try:
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, message_lower, re.IGNORECASE)
                    if match:
                        return self._extract_intent_data(intent, match, message_lower)
            
            return {"intent": "chat", "message": message_lower}
            
        except Exception as e:
            logger.error(f"Error in regex classification: {str(e)}")
            return {"intent": "chat", "message": message_lower}
    
    def _classify_with_gemini(self, message: str) -> Dict[str, Any]:
        """
        Classify intent using Gemini AI (intelligent method)
        """
        try:
            prompt = f"""You are an AI assistant for Bitzapp, a Bitcoin wallet service. Classify the user's message into one of these intents:

INTENTS:
- create_wallet: User wants to create/open a Bitcoin wallet
- deposit: User wants to deposit Naira to get Bitcoin
- send: User wants to send Bitcoin to someone
- balance: User wants to check their Bitcoin balance
- withdraw: User wants to withdraw Bitcoin to bank account
- receive: User wants to get their Bitcoin address
- transactions: User wants to see transaction history
- chat: General questions about Bitcoin, not financial actions

USER MESSAGE: "{message}"

Respond with ONLY a JSON object in this format:
{{
    "intent": "intent_name",
    "amount": number_if_relevant,
    "currency": "NGN_or_BTC_if_relevant",
    "receiver": "name_or_address_if_relevant"
}}

Examples:
- "I want to deposit 5000 naira" → {{"intent": "deposit", "amount": 5000, "currency": "NGN"}}
- "Send 0.001 BTC to John" → {{"intent": "send", "amount": 0.001, "currency": "BTC", "receiver": "John"}}
- "What is Bitcoin?" → {{"intent": "chat"}}
- "Check my balance" → {{"intent": "balance"}}

JSON Response:"""

            response = self._call_gemini_api(prompt)
            
            if response:
                # Try to parse JSON response
                try:
                    # Extract JSON from response (in case there's extra text)
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        result = json.loads(json_str)
                        
                        # Validate intent
                        valid_intents = ['create_wallet', 'deposit', 'send', 'balance', 'withdraw', 'receive', 'transactions', 'chat']
                        if result.get('intent') in valid_intents:
                            return result
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error parsing Gemini JSON response: {str(e)}")
            
            return {"intent": "chat", "message": message}
            
        except Exception as e:
            logger.error(f"Error in Gemini classification: {str(e)}")
            return {"intent": "chat", "message": message}
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Call Gemini API for intent classification
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
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
                else:
                    logger.error("No candidates in Gemini response")
                    return ""
            else:
                logger.error(f"Gemini API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return ""
    
    def _handle_slash_command(self, message: str) -> Dict[str, Any]:
        """
        Handle slash commands
        """
        parts = message.split()
        command = parts[0].lower()
        
        if command == '/create':
            return {"intent": "create_wallet"}
        elif command == '/balance':
            return {"intent": "balance"}
        elif command == '/receive':
            return {"intent": "receive"}
        elif command == '/history':
            return {"intent": "transactions"}
        elif command.startswith('/deposit') and len(parts) > 1:
            amount = self._extract_amount(parts[1])
            return {"intent": "deposit", "amount": amount, "currency": "NGN"}
        elif command.startswith('/send') and len(parts) > 2:
            amount = self._extract_amount(parts[1])
            receiver = parts[2]
            return {"intent": "send", "amount": amount, "receiver": receiver, "currency": "BTC"}
        elif command.startswith('/withdraw') and len(parts) > 1:
            amount = self._extract_amount(parts[1])
            return {"intent": "withdraw", "amount": amount, "currency": "NGN"}
        else:
            return {"intent": "chat", "message": message}
    
    def _extract_intent_data(self, intent: str, match, message: str) -> Dict[str, Any]:
        """
        Extract data from matched intent
        """
        result = {"intent": intent}
        
        if intent == "deposit":
            amount = self._extract_amount(match.group(1))
            result.update({"amount": amount, "currency": "NGN"})
        
        elif intent == "send":
            if len(match.groups()) >= 2:
                amount = self._extract_amount(match.group(1))
                receiver = match.group(2).strip()
                result.update({"amount": amount, "receiver": receiver, "currency": "NGN"})
        
        elif intent == "withdraw":
            amount = self._extract_amount(match.group(1))
            result.update({"amount": amount, "currency": "NGN"})
        
        return result
    
    def _extract_amount(self, amount_str: str) -> float:
        """
        Extract numeric amount from string
        """
        try:
            # Remove commas and convert to float
            amount_str = amount_str.replace(',', '')
            return float(amount_str)
        except (ValueError, AttributeError):
            return 0.0
    
    def generate_chat_response(self, message: str) -> str:
        """
        Generate conversational response for chat intents
        """
        message_lower = message.lower()
        
        # Bitcoin basics
        if any(word in message_lower for word in ['what is bitcoin', 'bitcoin', 'btc']):
            return "Bitcoin is a decentralized digital currency that allows peer-to-peer transactions without banks. It's secure, global, and you control your own money."
        
        # Lightning Network
        elif any(word in message_lower for word in ['lightning', 'lightning network']):
            return "The Lightning Network enables instant, low-fee Bitcoin payments. It's perfect for small transactions and makes Bitcoin as fast as sending a text message."
        
        # Security
        elif any(word in message_lower for word in ['secure', 'security', 'safe']):
            return "Your Bitcoin is secure because you control your private keys. We never store your seed phrase, so only you can access your funds."
        
        # Price
        elif any(word in message_lower for word in ['price', 'rate', 'exchange rate']):
            return "Bitcoin prices change in real-time. You can check current rates when you deposit or withdraw. The system automatically converts at the best available rate."
        
        # How it works
        elif any(word in message_lower for word in ['how does', 'how to', 'how can']):
            return "Bitzapp makes Bitcoin simple! Create a wallet, deposit Naira to get Bitcoin, send Bitcoin instantly, or withdraw to your Nigerian bank account."
        
        # Default response
        else:
            return "I'm here to help with your Bitcoin wallet! You can create a wallet, deposit Naira, send Bitcoin, or ask me about Bitcoin basics. What would you like to do?"
    
    def format_financial_response(self, intent_data: Dict[str, Any]) -> str:
        """
        Format financial intent as JSON string for backend processing
        """
        return json.dumps(intent_data, indent=2)
