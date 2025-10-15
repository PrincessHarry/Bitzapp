"""
Bitnob API Service for Bitzapp
Handles all Bitcoin and Lightning Network operations through Bitnob API
"""
import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('bitzapp')


class BitnobService:
    """
    Service for interacting with Bitnob API for Bitcoin operations
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'BITNOB_API_KEY', '')
        self.base_url = getattr(settings, 'BITNOB_BASE_URL', 'https://sandboxapi.bitnob.co')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_wallet(self, user_phone: str) -> Dict[str, Any]:
        """
        Create a new Bitcoin wallet for user
        """
        try:
            url = f"{self.base_url}/api/v1/wallets"
            data = {
                "phone": user_phone,
                "currency": "BTC"
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                wallet_data = response.json()
                return {
                    "success": True,
                    "wallet_id": wallet_data.get("id"),
                    "bitcoin_address": wallet_data.get("address"),
                    "balance": wallet_data.get("balance", 0)
                }
            else:
                logger.error(f"Bitnob wallet creation failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create wallet"}
                
        except Exception as e:
            logger.error(f"Error creating Bitnob wallet: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_wallet_balance(self, user_phone: str) -> Dict[str, Any]:
        """
        Get user's Bitcoin wallet balance
        """
        try:
            url = f"{self.base_url}/api/v1/wallets"
            params = {"phone": user_phone}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                wallets = response.json()
                if wallets:
                    wallet = wallets[0]
                    return {
                        "success": True,
                        "balance_btc": float(wallet.get("balance", 0)),
                        "bitcoin_address": wallet.get("address"),
                        "wallet_id": wallet.get("id")
                    }
                else:
                    return {"success": False, "error": "No wallet found"}
            else:
                logger.error(f"Bitnob balance check failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to get balance"}
                
        except Exception as e:
            logger.error(f"Error getting Bitnob balance: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_bitcoin(self, user_phone: str, recipient_address: str, amount_btc: float, description: str = "") -> Dict[str, Any]:
        """
        Send Bitcoin to another address
        """
        try:
            url = f"{self.base_url}/api/v1/transactions/send"
            data = {
                "phone": user_phone,
                "address": recipient_address,
                "amount": amount_btc,
                "currency": "BTC",
                "description": description
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                tx_data = response.json()
                return {
                    "success": True,
                    "transaction_id": tx_data.get("id"),
                    "tx_hash": tx_data.get("hash"),
                    "amount": amount_btc,
                    "status": "pending"
                }
            else:
                logger.error(f"Bitnob send failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to send Bitcoin"}
                
        except Exception as e:
            logger.error(f"Error sending Bitcoin: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_lightning_invoice(self, user_phone: str, amount_sats: int, description: str = "") -> Dict[str, Any]:
        """
        Create Lightning Network invoice
        """
        try:
            url = f"{self.base_url}/api/v1/lightning/invoices"
            data = {
                "phone": user_phone,
                "amount": amount_sats,
                "description": description
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                invoice_data = response.json()
                return {
                    "success": True,
                    "invoice_id": invoice_data.get("id"),
                    "payment_request": invoice_data.get("payment_request"),
                    "amount_sats": amount_sats,
                    "status": "pending"
                }
            else:
                logger.error(f"Bitnob Lightning invoice creation failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create Lightning invoice"}
                
        except Exception as e:
            logger.error(f"Error creating Lightning invoice: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def pay_lightning_invoice(self, user_phone: str, payment_request: str, description: str = "") -> Dict[str, Any]:
        """
        Pay a Lightning Network invoice
        """
        try:
            url = f"{self.base_url}/api/v1/lightning/payments"
            data = {
                "phone": user_phone,
                "payment_request": payment_request,
                "description": description
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                payment_data = response.json()
                return {
                    "success": True,
                    "payment_id": payment_data.get("id"),
                    "amount_sats": payment_data.get("amount"),
                    "status": "completed"
                }
            else:
                logger.error(f"Bitnob Lightning payment failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to pay Lightning invoice"}
                
        except Exception as e:
            logger.error(f"Error paying Lightning invoice: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def deposit_naira(self, user_phone: str, amount_ngn: float) -> Dict[str, Any]:
        """
        Create Naira deposit request (converts to Bitcoin)
        """
        try:
            url = f"{self.base_url}/api/v1/deposits"
            data = {
                "phone": user_phone,
                "amount": amount_ngn,
                "currency": "NGN"
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                deposit_data = response.json()
                return {
                    "success": True,
                    "deposit_id": deposit_data.get("id"),
                    "amount_ngn": amount_ngn,
                    "amount_btc": deposit_data.get("bitcoin_amount", 0),
                    "exchange_rate": deposit_data.get("exchange_rate", 0),
                    "status": "pending"
                }
            else:
                logger.error(f"Bitnob deposit failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create deposit"}
                
        except Exception as e:
            logger.error(f"Error creating deposit: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def withdraw_to_bank(self, user_phone: str, amount_ngn: float, bank_code: str, account_number: str, account_name: str) -> Dict[str, Any]:
        """
        Withdraw Bitcoin to Nigerian bank account (converts to Naira)
        """
        try:
            url = f"{self.base_url}/api/v1/withdrawals"
            data = {
                "phone": user_phone,
                "amount": amount_ngn,
                "currency": "NGN",
                "bank_code": bank_code,
                "account_number": account_number,
                "account_name": account_name
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                withdrawal_data = response.json()
                return {
                    "success": True,
                    "withdrawal_id": withdrawal_data.get("id"),
                    "amount_ngn": amount_ngn,
                    "amount_btc": withdrawal_data.get("bitcoin_amount", 0),
                    "exchange_rate": withdrawal_data.get("exchange_rate", 0),
                    "status": "pending"
                }
            else:
                logger.error(f"Bitnob withdrawal failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create withdrawal"}
                
        except Exception as e:
            logger.error(f"Error creating withdrawal: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_transaction_history(self, user_phone: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get user's transaction history
        """
        try:
            url = f"{self.base_url}/api/v1/transactions"
            params = {
                "phone": user_phone,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                transactions = response.json()
                return {
                    "success": True,
                    "transactions": transactions
                }
            else:
                logger.error(f"Bitnob transaction history failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to get transaction history"}
                
        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_exchange_rate(self) -> Dict[str, Any]:
        """
        Get current Bitcoin to Naira exchange rate
        """
        try:
            url = f"{self.base_url}/api/v1/rates"
            params = {"from": "BTC", "to": "NGN"}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                rate_data = response.json()
                return {
                    "success": True,
                    "rate": float(rate_data.get("rate", 0)),
                    "currency": "BTC/NGN"
                }
            else:
                logger.error(f"Bitnob exchange rate failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to get exchange rate"}
                
        except Exception as e:
            logger.error(f"Error getting exchange rate: {str(e)}")
            return {"success": False, "error": str(e)}
