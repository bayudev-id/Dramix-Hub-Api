import requests
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from core.config import settings

class MovieBoxAPIException(Exception):
    """Custom exception for MovieBox API errors."""
    pass

# Opener tanpa proxy (bypass semua proxy Windows)
_no_proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

class MovieBoxClient:
    def __init__(self, token: Optional[str] = None, lang: str = "id"):
        self.token = token
        self.lang = lang
        
        # Web session (h5-api.aoneroom.com)
        self.session = requests.Session()
        self.update_session_headers()
        
    def set_lang(self, lang: str):
        """Update language for the client."""
        self.lang = lang
        self.update_session_headers()

    def update_session_headers(self):
        """Update session headers based on current settings."""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": f"{self.lang},en-US;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "X-Client-Info": json.dumps({
                "timezone": "Asia/Jakarta",
                "userType": 1,
                "vipLevel": 2,
                "region": "ID",
                "sp_code": "51010",
                "net": "NETWORK_WIFI"
            }),
            "X-Geo-Ip": "103.149.120.1",
            "X-Geo-Country": "ID",
            "X-Request-Lang": self.lang,
            "X-Vip-Restrict": "0",
            "X-No-High-Risk-Restrict": "1",
            "X-Watch-Restrict": "0",
            "X-Vip-Restrict": "1",
            "X-No-High-Risk-Restrict": "0",
            "X-Source": "null",
            "Origin": settings.ORIGIN,
            "Referer": settings.REFERER,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Ch-Ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Brave";v="152"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Gpc": "1"
        })
        
        # Tambahkan cookies dari log browser
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjc2MzI1OTM5MTY3MDUyNjIyNzIsInV0cCI6MSwiZXhwIjoxNzk1ODYwMTEwLCJpYXQiOjE3ODgwODM4MTB9.S2RX2M4lTaUJUmigH-cThiTEQrv-ehUWBNGJkcXBpKY"
        token_val = self.token if self.token else default_token
        user_id = "2378083704688330200"
        
        try:
            import base64
            parts = token_val.split('.')
            if len(parts) > 1:
                payload_b64 = parts[1]
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                if 'uid' in payload:
                    user_id = str(payload['uid'])
                elif 'userId' in payload:
                    user_id = str(payload['userId'])
        except Exception:
            pass

        self.session.headers.update({
            "Authorization": f"Bearer {token_val}",
            "X-User": json.dumps({
                "token": token_val,
                "userId": user_id,
                "userType": 0,
                "appType": 3
            })
        })
        
        # Tambahkan cookies dari log browser
        self.session.cookies.set("mb_token", token_val)
        self.session.cookies.set("token", token_val)
        self.session.cookies.set("uuid", "b9875887-2624-4285-8e47-5e24c2707dd8")
        self.session.cookies.set("i18n_lang", "id")
        
        # Mobile headers untuk urllib
        mobile_info = {
            "package_name": "com.community.oneroom",
            "version_name": "3.0.14.0410.03",
            "version_code": 999999999,
            "os": "android",
            "os_version": "13",
            "install_ch": "google-play",
            "device_id": "80d065da0c94100b01a7a33f169277d4",
            "install_store": "gp",
            "gaid": "784b504c-b5fe-4e4a-b1ba-880c3a78ef61",
            "brand": "Xiaomi",
            "model": "Redmi 5 Plus",
            "system_language": self.lang,
            "net": "NETWORK_WIFI",
            "region": "ID",
            "timezone": "Asia/Jakarta",
            "sp_code": "51010"
        }
        
        self._mobile_headers = {
            "User-Agent": settings.MOBILE_USER_AGENT,
            "Accept": "application/json",
            "x-play-mode": "1",
            "x-idle-data": "1",
            "x-family-mode": "0",
            "x-content-mode": "0",
            "x-client-status": "1",
            "X-Client-Info": json.dumps(mobile_info),
            "Accept-Encoding": "gzip, deflate"
        }
        
        self._mobile_headers["Authorization"] = f"Bearer {token_val}"

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        url = f"{settings.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
            
        # Only use 'lang' parameter
        if "lang" not in params:
            params["lang"] = self.lang
            
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None and v != ""}

        response = self.session.request(method, url, params=params, **kwargs)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API level errors
        code = data.get("code")
        if code not in [0, 200]:
            raise MovieBoxAPIException(f"API Error: {data.get('message', 'Unknown error')} (Code: {code})")
            
        # Some endpoints return data in 'data' field, others return the root object
        # Based on logs, wefeed-h5api-bff usually uses 'data'
        return data.get("data", data)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return self._request("GET", endpoint, params=params, **kwargs)

    def get_full(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Fetch FULL JSON response including code and message."""
        url = f"{settings.BASE_URL}{endpoint}"
        if params is None: params = {}
        if "lang" not in params: params["lang"] = self.lang
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        
        response = self.session.request("GET", url, params=params, **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, json: Optional[Dict] = None, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST request - does not auto-add host/lang to query params, only to headers"""
        url = f"{settings.BASE_URL}{endpoint}"
        
        # For POST requests, don't add host/lang as query params
        # They should only be in headers or JSON body
        if params is None:
            params = {}
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        response = self.session.request("POST", url, json=json, params=params, **kwargs)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API level errors
        code = data.get("code")
        if code not in [0, 200]:
            raise MovieBoxAPIException(f"API Error: {data.get('message', 'Unknown error')} (Code: {code})")
            
        return data.get("data", data)

    def mobile_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request via mobile API (api4sg), menggunakan urllib untuk bypass proxy."""
        if params is None:
            params = {}
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        query_string = urllib.parse.urlencode(params)
        url = f"{settings.MOBILE_BASE_URL}{endpoint}"
        if query_string:
            url = f"{url}?{query_string}"
        
        req = urllib.request.Request(url)
        for key, value in self._mobile_headers.items():
            req.add_header(key, value)
        
        response = _no_proxy_opener.open(req)
        raw_data = response.read()
        
        # Handle gzip/deflate encoding
        encoding = response.headers.get("Content-Encoding", "")
        if encoding == "gzip":
            import gzip
            raw_data = gzip.decompress(raw_data)
        elif encoding == "deflate":
            import zlib
            raw_data = zlib.decompress(raw_data)
        
        data = json.loads(raw_data.decode("utf-8"))
        
        if data.get("code") != 0:
            raise MovieBoxAPIException(f"API Error: {data.get('message', 'Unknown error')} (Code: {data.get('code')})")
            
        return data.get("data", {})
