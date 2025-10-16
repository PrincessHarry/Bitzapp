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
            # Legacy simple deposit endpoint kept for backward compatibility
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

    def create_bank_transfer_checkout(
        self,
        amount_ngn: float,
        customer_email: str,
        narration: Optional[str] = None,
        expires_in_minutes: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Bitnob Checkout for NGN bank transfer with narration and expiry.

        According to Bitnob docs, Checkout supports local payments with bank transfer.
        We request virtual account details, narration and a countdown for expiry
        similar to Bitnob app screenshots.
        """
        try:
            url = f"{self.base_url}/api/v1/checkout"
            data: Dict[str, Any] = {
                "amount": amount_ngn,
                "currency": "NGN",
                "customerEmail": customer_email,
                "paymentMethod": "bank_transfer",
                "expiresIn": expires_in_minutes * 60
            }
            if narration:
                data["narration"] = narration
            if metadata:
                data["metadata"] = metadata

            response = requests.post(url, headers=self.headers, json=data, timeout=30)

            if response.status_code in (200, 201):
                payload = response.json()
                # Some Bitnob endpoints wrap in { status, data }
                container = payload.get("data", payload)
                return {
                    "success": True,
                    "checkout_id": container.get("id"),
                    "account_number": container.get("accountNumber"),
                    "bank_name": container.get("bankName"),
                    "account_name": container.get("accountName"),
                    "narration": container.get("narration"),
                    "amount_ngn": container.get("amount", amount_ngn),
                    "expires_at": container.get("expiresAt"),
                    "exchange_rate": container.get("exchangeRate"),
                    "status": container.get("status", "pending")
                }
            else:
                logger.error(f"Bitnob checkout creation failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create checkout"}
        except Exception as e:
            logger.error(f"Error creating checkout: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_checkout(self, checkout_id: str) -> Dict[str, Any]:
        """
        Fetch checkout details/status.
        """
        try:
            url = f"{self.base_url}/api/v1/checkout/{checkout_id}"
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                payload = response.json()
                container = payload.get("data", payload)
                return {
                    "success": True,
                    "data": container
                }
            else:
                logger.error(f"Bitnob checkout fetch failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to fetch checkout"}
        except Exception as e:
            logger.error(f"Error fetching checkout: {str(e)}")
            return {"success": False, "error": str(e)}

    def cancel_checkout(self, checkout_id: str) -> Dict[str, Any]:
        """
        Cancel/expire a pending checkout so account details are no longer valid.
        """
        try:
            url = f"{self.base_url}/api/v1/checkout/{checkout_id}/cancel"
            response = requests.post(url, headers=self.headers, json={}, timeout=30)

            if response.status_code in (200, 204):
                return {"success": True, "cancelled": True}
            else:
                logger.error(f"Bitnob checkout cancel failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to cancel checkout"}
        except Exception as e:
            logger.error(f"Error cancelling checkout: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_lnurl_address(self, user_phone: str, identifier: str, sat_min: int = 1000, sat_max: int = 1000000) -> Dict[str, Any]:
        """
        Create LNURL address for receiving Lightning payments
        """
        try:
            url = f"{self.base_url}/api/v1/lnurl"
            data = {
                "identifier": identifier,
                "identifierType": "username",
                "tld": "bitzapp-i3i3.onrender.com",
                "customerEmail": f"{user_phone}@bitzapp.com",
                "satMinSendable": sat_min,
                "satMaxSendable": sat_max
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                lnurl_data = response.json()
                if lnurl_data.get("status"):
                    return {
                        "success": True,
                        "lnurl": lnurl_data["data"]["lnUrl"],
                        "lnurl_qr": lnurl_data["data"]["lnUrlQR"],
                        "identifier": lnurl_data["data"]["identifier"],
                        "sat_min": lnurl_data["data"]["satMinSendable"],
                        "sat_max": lnurl_data["data"]["satMaxSendable"]
                    }
                else:
                    return {"success": False, "error": "Failed to create LNURL"}
            else:
                logger.error(f"Bitnob LNURL creation failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create LNURL"}
                
        except Exception as e:
            logger.error(f"Error creating LNURL: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def decode_lnurl(self, encoded_lnurl: str) -> Dict[str, Any]:
        """
        Decode LNURL to get payment details
        """
        try:
            url = f"{self.base_url}/api/v1/lnurl/decode"
            data = {
                "encodedLnUrl": encoded_lnurl
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                decode_data = response.json()
                if decode_data.get("status"):
                    return {
                        "success": True,
                        "identifier": decode_data["data"]["identifier"],
                        "description": decode_data["data"]["description"],
                        "callback": decode_data["data"]["callback"],
                        "sat_min": decode_data["data"]["satMinSendable"],
                        "sat_max": decode_data["data"]["satMaxSendable"],
                        "comment_allowed": decode_data["data"]["commentAllowed"]
                    }
                else:
                    return {"success": False, "error": "Failed to decode LNURL"}
            else:
                logger.error(f"Bitnob LNURL decode failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to decode LNURL"}
                
        except Exception as e:
            logger.error(f"Error decoding LNURL: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def pay_lnurl(self, user_phone: str, encoded_lnurl: str, satoshis: int, reference: str, comment: str = "") -> Dict[str, Any]:
        """
        Pay to LNURL address
        """
        try:
            url = f"{self.base_url}/api/v1/lnurl/pay"
            data = {
                "encodedLnUrl": encoded_lnurl,
                "satoshis": satoshis,
                "reference": reference,
                "comment": comment,
                "customerEmail": f"{user_phone}@bitzapp.com"
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                payment_data = response.json()
                return {
                    "success": True,
                    "payment_id": payment_data.get("id"),
                    "amount_sats": satoshis,
                    "status": "completed"
                }
            else:
                logger.error(f"Bitnob LNURL payment failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to pay LNURL"}
                
        except Exception as e:
            logger.error(f"Error paying LNURL: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_lnurl_withdrawal(self, user_phone: str, amount_sats: int, description: str = "") -> Dict[str, Any]:
        """
        Create LNURL withdrawal QR for sending Bitcoin to user
        """
        try:
            url = f"{self.base_url}/api/v1/lnurl/withdrawal"
            data = {
                "amount": amount_sats,
                "description": description,
                "customerEmail": f"{user_phone}@bitzapp.com"
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                withdrawal_data = response.json()
                if withdrawal_data.get("status"):
                    return {
                        "success": True,
                        "lnurl": withdrawal_data["data"]["lnUrl"],
                        "lnurl_qr": withdrawal_data["data"]["lnUrlQR"],
                        "amount_sats": amount_sats,
                        "description": description,
                        "withdrawal_id": withdrawal_data["data"]["id"]
                    }
                else:
                    return {"success": False, "error": "Failed to create LNURL withdrawal"}
            else:
                logger.error(f"Bitnob LNURL withdrawal failed: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to create LNURL withdrawal"}
                
        except Exception as e:
            logger.error(f"Error creating LNURL withdrawal: {str(e)}")
            return {"success": False, "error": str(e)}
