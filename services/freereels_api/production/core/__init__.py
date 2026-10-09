"""
FreeReels Production Client - Core Module
"""

from .client import FreeReelsClient
from .auth import OAuthSigner

__version__ = "1.4.0"
__all__ = ["FreeReelsClient", "OAuthSigner"]
