#!/usr/bin/env python3
"""
Test JWKS client in Docker environment
"""

import jwt
from jwt import PyJWKClient
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_jwks_in_docker():
    """Test JWKS client in Docker environment."""
    print("🔍 Testing JWKS Client in Docker Environment")
    
    jwks_url = "https://dev-bktskx5kbc655wcl.us.auth0.com/.well-known/jwks.json"
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjNDOVRNSDBodHNsbWhUT3FYUENnNiJ9.eyJpc3MiOiJodHRwczovL2Rldi1ia3Rza3g1a2JjNjU1d2NsLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJJTndzODQ5eURYYUM2TVpWWG5MaE1KaTZDWkM0bng2VUBjbGllbnRzIiwiYXVkIjoiSU53czg0OXlEWGFDNk1aVlhuTGhNSmk2Q1pDNG54NlUiLCJpYXQiOjE3NTc5OTQwOTYsImV4cCI6MTc1ODA4MDQ5NiwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIiwiYXpwIjoiSU53czg0OXlEWGFDNk1aVlhuTGhNSmk2Q1pDNG54NlUifQ.XxLsk2L4eatevYMwVCTA_M8tAe2JN9DFaji_avrrUuEU7lQsHdD7WIYlclittAefTdNcp2qKfNSpIlak_N-s95rol12i_3R2eFxNV2477PiBbt_KGjIUxw9hGpsXuu2Ghbiu77ei1DArU1gcQNmZPXXbaeM8wlCFtaedqBpSU05LDM8g26CP4OBaq9qM11qEXuISbsZth4ViICSvQE_qazrkYkCMO_bYwhHItrpqQ1wsVbGFe1S1i05uiTlSHK7cuI5j3AeD8B_1KpuSQTLvjQ8WKVyUYfSpvfxpGB0v3z72vgTLkJ4nEYXQUscbtstj2NtBKA2TlNS-5FrvTWtj4g"
    
    try:
        print(f"JWKS URL: {jwks_url}")
        print(f"Token: {token[:50]}...")
        
        # Test 1: Initialize JWKS client
        print("\n1. Initializing JWKS client...")
        jwks_client = PyJWKClient(jwks_url)
        print("✅ JWKS client initialized")
        
        # Test 2: Get signing key
        print("\n2. Getting signing key...")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"✅ Signing key retrieved: {type(signing_key)}")
        print(f"   Key type: {type(signing_key.key)}")
        
        # Test 3: Decode token
        print("\n3. Decoding token...")
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="INws849yDXaC6MZVXnLhMJi6CZC4nx6U",
            issuer="https://dev-bktskx5kbc655wcl.us.auth0.com/",
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True
            }
        )
        print("✅ Token decoded successfully")
        print(f"   Payload: {payload}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jwks_in_docker()
