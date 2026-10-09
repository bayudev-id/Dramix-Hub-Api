# -*- coding: utf-8 -*-
"""
Auth Module for FreeReels
Implements the OAuth Signature logic based on HeaderInterceptor analysis.
"""

import hashlib
import time
from typing import Optional

# Constants from reverse engineering
OAUTH_SECRET_PREFIX = "8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&"

class AuthError(Exception):
    """Exception raised for authentication configuration errors."""
    pass

def compute_oauth_signature(oauth_secret: str) -> str:
    """Compute the MD5 hex signature from the secret."""
    raw = f"{OAUTH_SECRET_PREFIX}{oauth_secret}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def build_authorization_header(oauth_token: str, oauth_secret: str, ts_ms: Optional[int] = None) -> str:
    """Build the custom FreeReels Authorization header."""
    if not oauth_token or not oauth_secret:
        raise AuthError("oauth_token and oauth_secret are required for authenticated requests.")

    if ts_ms is None:
        ts_ms = int(time.time() * 1000)

    signature = compute_oauth_signature(oauth_secret)
    return f"oauth_signature={signature},oauth_token={oauth_token},ts={ts_ms}"

class OAuthSigner:
    """Manages OAuth state and generates headers."""
    
    def __init__(self, oauth_token: Optional[str] = None, oauth_secret: Optional[str] = None):
        self.oauth_token = oauth_token
        self.oauth_secret = oauth_secret

    def update(self, oauth_token: Optional[str] = None, oauth_secret: Optional[str] = None):
        """Update credentials (e.g., after login)."""
        if oauth_token:
            self.oauth_token = oauth_token
        if oauth_secret:
            self.oauth_secret = oauth_secret

    def get_header(self, now_ms: Optional[int] = None) -> str:
        """Generate the current Authorization header."""
        return build_authorization_header(self.oauth_token, self.oauth_secret, ts_ms=now_ms)

    def is_configured(self) -> bool:
        """Check if credentials are set."""
        return bool(self.oauth_token and self.oauth_secret)
