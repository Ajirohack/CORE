"""
Authentication utilities for core services
"""
import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

class ServiceAuth:
    """Handles authentication for core services"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        
    def generate_api_key(self, service_name: str) -> str:
        """Generate API key for a service"""
        timestamp = datetime.utcnow().isoformat()
        raw_key = f"{service_name}:{timestamp}:{secrets.token_urlsafe(16)}"
        return hashlib.sha256(raw_key.encode()).hexdigest()
    
    def generate_jwt(self, service_id: str, service_name: str, expires_hours: int = 24) -> str:
        """Generate JWT token for service authentication"""
        if not JWT_AVAILABLE:
            return f"simple_token_{service_id}_{secrets.token_urlsafe(16)}"
        
        payload = {
            'service_id': service_id,
            'service_name': service_name,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        if not JWT_AVAILABLE:
            # Simple verification for development
            if token.startswith('simple_token_'):
                parts = token.split('_')
                if len(parts) >= 3:
                    return {'service_id': parts[2], 'service_name': 'unknown'}
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_api_key(self, api_key: str, expected_service: str) -> bool:
        """Verify API key (basic implementation)"""
        # In production, this would check against a database
        return len(api_key) == 64 and api_key.isalnum()
