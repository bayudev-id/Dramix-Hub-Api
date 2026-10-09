"""RSA password encryption for iQIYI authentication."""
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


class PasswordEncryptor:
    """Encrypts plaintext password using iQIYI RSA public key."""

    # iQIYI RSA public key (temporary test key, replace with real key extracted from APK)
    PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy2jJaUAvOxwE9hQRHIKc
QNLdCgPZOtDu3PJUjSF3cSW8aJFJiDNbNm8DyR1/Fo6V+A4EMf5K2txJ/3bRWzZn
urcl5Z4KjdnBwh5k9C52+LFw6iLOn25F9R0t5MYpuSjNSr2OWHJn0Y+JqeSXl+E5
mSjD9gD9PeUiXFFHEVvam9/oUXFUSxm4UxkG64z7tLBHsIfVLvAbh6At5EppxmfS
U8DPSAykZFthgiNd+vaD7UqduGApnIIB6qqSApNf7FXBMo6490GGo/5g6QRL8O+i
yCt1s2bkKqVA/vVmBG5P/xHnOq9MKpuxh4JKop2kuvIJ2zFQkVYs7pA/maMK4M0S
4wIDAQAB
-----END PUBLIC KEY-----"""

    @staticmethod
    def encrypt_password(plaintext: str, public_key_pem: str = PUBLIC_KEY_PEM) -> str:
        """
        Encrypt plaintext password using RSA public key.
        
        Args:
            plaintext: Plaintext password to encrypt
            public_key_pem: RSA public key in PEM format
            
        Returns:
            Base64-encoded encrypted password
            
        Raises:
            ValueError: If encryption fails
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Encrypt using PKCS1v15 padding
            encrypted = public_key.encrypt(
                plaintext.encode(),
                padding.PKCS1v15()
            )
            
            # Return base64-encoded result
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Password encryption failed: {e}")

    @staticmethod
    def validate_encrypted_password(encrypted: str) -> bool:
        """
        Validate encrypted password format (base64).
        
        Args:
            encrypted: Encrypted password string to validate
            
        Returns:
            True if valid base64, False otherwise
        """
        try:
            base64.b64decode(encrypted)
            return True
        except Exception:
            return False
