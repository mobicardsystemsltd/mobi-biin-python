import json
import base64
import hmac
import hashlib
import random
import requests

class MobicardBiinLookup:
    def __init__(self, merchant_id, api_key, secret_key):
        self.mobicard_version = "2.0"
        self.mobicard_mode = "LIVE"
        self.mobicard_merchant_id = merchant_id
        self.mobicard_api_key = api_key
        self.mobicard_secret_key = secret_key
        self.mobicard_service_id = "20000"
        self.mobicard_service_type = "BIINLOOKUP"
        
        self.mobicard_token_id = str(random.randint(1000000, 1000000000))
        self.mobicard_txn_reference = str(random.randint(1000000, 1000000000))
    
    def lookup_biin(self, card_input):
        """Lookup card issuer information using BIN/BIIN"""
        
        # Accepts 6-digit BIN, 8-digit BIIN, or full card number
        if len(card_input) >= 8:
            mobicard_card_biin = card_input[:8]
        elif len(card_input) >= 6:
            mobicard_card_biin = card_input[:6]
        else:
            return {'status': 'ERROR', 'error_message': 'Invalid card input - must be at least 6 digits'}
        
        # Create JWT Header
        jwt_header = {"typ": "JWT", "alg": "HS256"}
        encoded_header = base64.urlsafe_b64encode(
            json.dumps(jwt_header).encode()
        ).decode().rstrip('=')
        
        # Create JWT Payload
        jwt_payload = {
            "mobicard_version": self.mobicard_version,
            "mobicard_mode": self.mobicard_mode,
            "mobicard_merchant_id": self.mobicard_merchant_id,
            "mobicard_api_key": self.mobicard_api_key,
            "mobicard_service_id": self.mobicard_service_id,
            "mobicard_service_type": self.mobicard_service_type,
            "mobicard_token_id": self.mobicard_token_id,
            "mobicard_txn_reference": self.mobicard_txn_reference,
            "mobicard_card_biin": mobicard_card_biin
        }
        
        encoded_payload = base64.urlsafe_b64encode(
            json.dumps(jwt_payload).encode()
        ).decode().rstrip('=')
        
        # Generate Signature
        header_payload = f"{encoded_header}.{encoded_payload}"
        signature = hmac.new(
            self.mobicard_secret_key.encode(),
            header_payload.encode(),
            hashlib.sha256
        ).digest()
        encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        jwt_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
        
        # Make API Call
        url = "https://mobicardsystems.com/api/v1/biin_lookup"
        payload = {"mobicard_auth_jwt": jwt_token}
        
        try:
            response = requests.post(url, json=payload, verify=False, timeout=30)
            response_data = response.json()
            
            if response_data.get('status') == 'SUCCESS':
                return {
                    'status': 'SUCCESS',
                    'card_scheme': response_data['card_biin_information']['card_biin_scheme'],
                    'issuer_bank': response_data['card_biin_information']['card_biin_bank_name'],
                    'card_type': response_data['card_biin_information']['card_biin_type'],
                    'country': response_data['card_biin_information']['card_biin_country_name'],
                    'is_prepaid': response_data['card_biin_information']['card_biin_prepaid'],
                    'raw_response': response_data
                }
            else:
                return {
                    'status': 'ERROR',
                    'status_code': response_data.get('status_code'),
                    'status_message': response_data.get('status_message')
                }
                
        except Exception as e:
            return {'status': 'ERROR', 'error_message': str(e)}

# Usage
biin_lookup = MobicardBiinLookup(
    merchant_id="4",
    api_key="YmJkOGY0OTZhMTU2ZjVjYTIyYzFhZGQyOWRiMmZjMmE2ZWU3NGIxZWM3ZTBiZSJ9",
    secret_key="NjIwYzEyMDRjNjNjMTdkZTZkMjZhOWNiYjIxNzI2NDQwYzVmNWNiMzRhMzBjYSJ9"
)

# Can use 6-digit BIN, 8-digit BIIN, or full card number
result = biin_lookup.lookup_biin("5173350006475601")  # Full card number
# result = biin_lookup.lookup_biin("51733500")  # 8-digit BIIN
# result = biin_lookup.lookup_biin("517335")    # 6-digit BIN

if result['status'] == 'SUCCESS':
    print(f"Card Scheme: {result['card_scheme']}")
    print(f"Issuer Bank: {result['issuer_bank']}")
    print(f"Card Type: {result['card_type']}")
    print(f"Country: {result['country']}")
    print(f"Prepaid: {result['is_prepaid']}")
    
    if result['is_prepaid'] == 'Yes':
        print("Note: Prepaid card detected - apply appropriate risk rules.")
else:
    print(f"Error: {result.get('status_message')}")
