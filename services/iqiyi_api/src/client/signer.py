"""Request signer for iQIYI API authentication."""
import hashlib
import hmac
import time
from typing import Dict, Any, Optional


class Signer:
    """Generates iQIYI request signatures and authentication headers."""

    # Default device parameters (from APK decompilation)
    DEFAULT_DEVICE_ID = "f66426a8bfcb12539fd50c78108494491102"
    DEFAULT_QYIDV2 = "36287525ACE2E0587B13C83881D2F453"
    DEFAULT_DFP = "1527eecbba655757bf9c9e864acd1d176ab402e8840227f714acd303fdd21da40d"
    DEFAULT_USER_AGENT = "QIYIVideo/8.1.5 (Gphone;com.iqiyi.i18n;Android 13;Xiaomi Redmi 5 Plus) Corejar"

    @staticmethod
    def generate_sign(params: Dict[str, Any], timestamp: Optional[int] = None) -> str:
        """
        Generate MD5 signature for request parameters.
        
        Args:
            params: Parameters dict to sign
            timestamp: Unix timestamp (default: current time)
            
        Returns:
            Hex MD5 signature string
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Build signature string from sorted params
        sorted_items = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_items)
        
        # MD5 hash
        sig = hashlib.md5(param_str.encode()).hexdigest()
        return sig

    @staticmethod
    def generate_pass_sign(timestamp: Optional[int] = None, device_id: str = DEFAULT_DEVICE_ID) -> str:
        """
        Generate Pass-Sign header value for login requests.
        
        Format: {hash}_{flag1}_{flag2}_{flag3}
        
        Args:
            timestamp: Unix timestamp (default: current time)
            device_id: Device ID string
            
        Returns:
            Pass-Sign header value
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Create hash from timestamp + device_id
        sign_data = f"{timestamp}{device_id}".encode()
        sig = hashlib.md5(sign_data).hexdigest()
        
        return f"{sig}_1_0_1"

    @staticmethod
    def build_headers(
        extra_headers: Optional[Dict[str, str]] = None,
        device_id: str = DEFAULT_DEVICE_ID,
        qyidv2: str = DEFAULT_QYIDV2,
    ) -> Dict[str, str]:
        """
        Build standard iQIYI request headers.
        
        Args:
            extra_headers: Additional headers to merge
            device_id: Device ID
            qyidv2: QYIDv2 header value
            
        Returns:
            Dict of headers
        """
        timestamp = int(time.time())
        
        headers = {
            "User-Agent": Signer.DEFAULT_USER_AGENT,
            "T": str(timestamp),
            "Qyid": device_id,
            "qyidv2": qyidv2,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate",
        }
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers

    @staticmethod
    def build_auth_body(
        username: str,
        encrypted_password: str,
        device_id: str = DEFAULT_DEVICE_ID,
        qyidv2: str = DEFAULT_QYIDV2,
        dfp: str = DEFAULT_DFP,
    ) -> str:
        """
        Build form-urlencoded login request body.
        
        Args:
            username: Phone number or email
            encrypted_password: Base64-encoded encrypted password
            device_id: Device ID
            qyidv2: QYIDv2 value
            dfp: Device fingerprint
            
        Returns:
            URL-encoded form body string
        """
        timestamp = int(time.time())
        
        params = {
            "account_id": username,
            "passwd": encrypted_password,
            "deviceid": device_id,
            "qyidv2": qyidv2,
            "dfp": dfp,
            "t": str(timestamp),
            "app_version": "8.8.5",
            "platform": "android",
            "os_version": "13",
        }
        
        # URL encode: key=value&key2=value2
        body = "&".join(f"{k}={v}" for k, v in params.items())
        return body

    @staticmethod
    def calculate_request_sign(body: str) -> str:
        """
        Calculate Sign header for request body.
        
        Args:
            body: Request body string
            
        Returns:
            Hex MD5 signature
        """
        return hashlib.md5(body.encode()).hexdigest()

    @staticmethod
    def _authkey_transform(query_string: str) -> str:
        """
        Apply iQIYI authkey transform to query string before MD5.
        Ported from iqiyi.js authkey() function.
        
        Args:
            query_string: Query string without leading '?'
            
        Returns:
            Transformed string for MD5 hashing
        """
        # authkey adds custom salt characters at specific positions
        # Based on decompiled JS: insert chars from salt array at indices
        salt = "fb8xc3dv5c6a8k2l"
        
        # Insert salt[0] at index 13
        if len(query_string) > 13:
            query_string = query_string[:13] + salt[0] + query_string[13:]
        
        # Insert salt[1] at index 9
        if len(query_string) > 9:
            query_string = query_string[:9] + salt[1] + query_string[9:]
        
        return query_string

    @staticmethod
    def generate_dash_vf(params: Dict[str, Any]) -> str:
        """
        Generate vf signature for /dash playback endpoint.
        
        Args:
            params: Query parameters dict (tvid, bid, tm, etc)
            
        Returns:
            Hex MD5 signature for vf parameter
        """
        # Build query string from params
        query_parts = [f"{k}={v}" for k, v in sorted(params.items())]
        query_string = "&".join(query_parts)
        
        # Apply authkey transform
        transformed = Signer._authkey_transform(query_string)
        
        # MD5 hash
        vf = hashlib.md5(transformed.encode()).hexdigest()
        return vf

    @staticmethod
    def generate_video_play_sign(params: Dict[str, Any]) -> str:
        """
        Generate Sign header for /video/play endpoint (mobile API).
        Used for both standard and short drama playback.
        
        Pattern from Burp: Sign = MD5(sorted_query_params)
        
        Args:
            params: Query parameters dict
            
        Returns:
            Hex MD5 signature for Sign header
        """
        sorted_items = sorted(params.items())
        query_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        return hashlib.md5(query_string.encode()).hexdigest()

    @staticmethod
    def generate_qdsf(params: Dict[str, Any], timestamp: Optional[int] = None, device_id: str = DEFAULT_DEVICE_ID) -> str:
        """
        Generate Qdsf header for /video/play mobile endpoint.
        
        Format: {hash}_{flag1}_{flag2}_{flag3}
        
        Args:
            params: Query parameters dict
            timestamp: Unix timestamp (default: current time)
            device_id: Device ID string
            
        Returns:
            Qdsf header value
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Build query string from sorted params
        query_parts = [f"{k}={v}" for k, v in sorted(params.items())]
        query_string = "&".join(query_parts)
        
        # Create hash from query_string + device_id
        sign_data = f"{query_string}{device_id}".encode()
        sig = hashlib.md5(sign_data).hexdigest()
        
        return f"{sig}_1_0_1"
