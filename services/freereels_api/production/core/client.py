#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeReels API Client - Interactive Drama Browser & Player
Menu interaktif untuk browsing drama, lihat detail, dan play episode

Author: Generated from JADX analysis
Version: 1.0.0
"""

import requests
import json
import sys
import os
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin
import webbrowser
import subprocess
import base64
from Crypto.Cipher import AES

# AES Keys extracted from libdwguard.so (native library)
AES_KEYS = {
    1: b"3sa9Kx7mQu3Ls8Wd",  # flavor 1
    2: b"79psatnvfgktswba",   # flavor 2
}

def unpad_pkcs7(data: bytes) -> bytes:
    """Remove PKCS7 padding"""
    if not data:
        return data
    pad_len = data[-1]
    if 1 <= pad_len <= 16 and data[-pad_len:] == bytes([pad_len]) * pad_len:
        return data[:-pad_len]
    return data

def decrypt_native_response(base64_cipher: str) -> Optional[str]:
    """
    Decrypts response encrypted by libdwguard.so.
    Format: base64(IV_16 || ciphertext)
    Uses AES-128-CBC with extracted keys.
    """
    try:
        raw = base64.b64decode(base64_cipher)
        if len(raw) < 32 or len(raw) % 16 != 0:
            return None
        
        iv = raw[:16]
        ciphertext = raw[16:]
        
        for key in AES_KEYS.values():
            try:
                cipher = AES.new(key, AES.MODE_CBC, iv)
                decrypted = cipher.decrypt(ciphertext)
                plaintext = unpad_pkcs7(decrypted)
                text = plaintext.decode("utf-8", errors="replace")
                if text.startswith("{") or text.startswith("["):
                    return text
            except Exception:
                continue
    except Exception:
        pass
    return None


# ============================================
# CONFIGURATION
# ============================================

# Base URLs yang ditemukan dari log Frida
BASE_URL = "https://apiv2.free-reels.com"  # ✅ Confirmed from log
TRACE_URL = "https://trace.free-reels.com"
VIDEO_BASE_URL = "https://video-v1.mydramawave.com"

# Headers yang lebih lengkap (dari analisis log)
DEFAULT_HEADERS = {
    "User-Agent": "FreeReels/2.4.91 (Android 13; Redmi 5 Plus)",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "id-ID",
    "app-version": "2.4.91",
    "app-name": "com.freereels.app",
    "device": "android",
    "device-version": "33",
    "device-id": "da9ce769379941e4",
    "country": "ID",
    "language": "id-ID",
    "app-display-lang": "id",
    "locale": "id_ID",
    "prefer_country": "ID",
    "app-language": "id",
    "timezone": "+7",
    "X-Timezone": "Asia/Jakarta",
    "network-type": "wifi",
    "screen-width": "432",
    "screen-height": "840",
    "x-device-model": "Redmi 5 Plus",
    "x-device-manufacturer": "Xiaomi",
    "x-device-brand": "Xiaomi",
    "x-device-product": "vince",
    "device-language": "id-ID",
    "device-country": "ID",
    "is-mainland": "false",
    "Connection": "Keep-Alive",
}

# ============================================
# LANGUAGE MAPPING (22 bahasa verified working)
# ============================================
SUPPORTED_LANGUAGES = {
    # Short code to full locale mapping
    "id": ("id-ID", "ID", "Indonesia"),
    "en": ("en-US", "US", "English"),
    "es": ("es-MX", "MX", "Español"),
    "pt": ("pt-PT", "PT", "Português"),
    "fr": ("fr-FR", "FR", "Français"),
    "de": ("de-DE", "DE", "Deutsch"),
    "it": ("it-IT", "IT", "Italiano"),
    "ru": ("ru-RU", "RU", "Русский"),
    "ar": ("ar-SA", "SA", "العربية"),
    "hi": ("hi-IN", "IN", "हिन्दी"),
    "ta": ("ta-IN", "IN", "தமிழ்"),
    "te": ("te-IN", "IN", "తెలుగు"),
    "bn": ("bn-BD", "BD", "বাংলা"),
    "th": ("th-TH", "TH", "ไทย"),
    "vi": ("vi-VN", "VN", "Tiếng Việt"),
    "tl": ("tl-PH", "PH", "Filipino"),
    "ms": ("ms-MY", "MY", "Bahasa Melayu"),
    "ja": ("ja-JP", "JP", "日本語"),
    "ko": ("ko-KR", "KR", "한국어"),
    "zh": ("zh-TW", "TW", "繁體中文"),
    "pl": ("pl-PL", "PL", "Polski"),
    "tr": ("tr-TR", "TR", "Türkçe"),
    # Removed: cs (Czech), ro (Romanian), el (Greek) - no content available
}

# ============================================
# API CLIENT CLASS
# ============================================

class FreeReelsClient:
    """Client untuk interact dengan FreeReels/DramaWave API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        # Use the new OAuthSigner for advanced authentication
        from .auth import OAuthSigner
        self.signer = OAuthSigner()
        
        self.user_id: Optional[str] = None
        self.device_id: Optional[str] = None
        self.current_language = "id-ID"
        
        # Set default to Indonesia
        self.set_language("id")  # Track current language
    
    def set_language(self, lang_code: str, country: str = None):
        """
        Ubah bahasa dan negara untuk mendapatkan katalog + judul dalam bahasa berbeda.
        Support 24 bahasa.
        
        Args:
            lang_code: Kode bahasa short ("id", "en", "ja") atau full ("id-ID", "en-US", "ja-JP")
            country: Kode negara (optional, auto-extracted dari lang_code jika full format)
        
        Contoh:
            client.set_language("en")        # English (auto: en-US, US)
            client.set_language("en-US")     # Explicit English
            client.set_language("ja")        # Japanese (auto: ja-JP, JP)
            client.set_language("es")        # Spanish (auto: es-MX, MX)
        """
        # Normalize input: if full locale provided (e.g., "en-US"), extract short code
        if "-" in lang_code:
            short_code = lang_code.split("-")[0]
            full_locale = lang_code
        else:
            short_code = lang_code
            full_locale = None
        
        # Look up in supported languages
        if short_code not in SUPPORTED_LANGUAGES:
            available = ", ".join(SUPPORTED_LANGUAGES.keys())
            print(f"[!] Language '{short_code}' not supported. Available: {available}")
            return False
        
        if not full_locale:
            full_locale, country, display_name = SUPPORTED_LANGUAGES[short_code]
        else:
            # Validate that the full locale exists in SUPPORTED_LANGUAGES
            found = False
            for sc, (fl, c, dn) in SUPPORTED_LANGUAGES.items():
                if fl == full_locale:
                    country = c
                    display_name = dn
                    found = True
                    break
            if not found:
                print(f"[!] Full locale '{full_locale}' not recognized")
                return False
        
        if not country:
            country = full_locale.split("-")[1]
        
        lang_only = full_locale.split("-")[0]
        
        headers = {
            "app-display-lang": lang_only,
            "language": full_locale,
            "device-language": full_locale,
            "country": country,
            "device-country": country,
            "locale": full_locale.replace("-", "_"),
            "prefer_country": country,
            "app-language": lang_only,
            "Accept-Language": full_locale,
        }
        
        self.current_language = full_locale
        print(f"[*] Language set to: {full_locale}")
    
    def get_homepage_tabs(self) -> list:
        """
        Ambil daftar tab/kategori homepage lengkap dari server.
        Termasuk kategori Populer, New, Segera hadir, Dubbing, Perempuan, Laki-Laki.
        
        Returns:
            List of tab dicts with keys: name, tab_key, business_name, etc.
        """
        resp = self._request("GET", "/frv2-api/homepage/v2/tab/list")
        if resp and "list" in resp:
            return resp["list"]
        return []

    def get_dramas_by_category(self, tab_key: str, position_index: str = "10000") -> list:
        """
        Ambil daftar drama berdasarkan kategori (tab_key).
        
        Available tab_keys:
            - "503": Populer (Popular)
            - "505": New (Baru)
            - "622": Segera hadir (Coming soon - 200+ drama)
            - "516": Dubbing (Sulih Suara)
            - "504": Perempuan (Female)
            - "506": Laki-Laki (Male)
        """
        resp = self._request("GET", "/frv2-api/homepage/v2/tab/index", params={
            "tab_key": str(tab_key),
            "position_index": str(position_index),
            "rec_trigger": "1"
        })
        
        dramas = []
        if resp and "items" in resp:
            for section in resp["items"]:
                for item in section.get("items", []):
                    dramas.append(item)
        return dramas

    def get_ranking(self, period: str = "daily") -> list:
        """
        Ambil Top 20 ranking dramas berdasarkan periode.
        
        Args:
            period: "daily", "weekly", "monthly", atau "annually"
        
        Returns:
            List of 20 dramas dengan ranking metadata
        """
        resp = self._request("POST", "/frv2-api/homepage/v2/rank", json={"key": period})
        if resp and "items" in resp:
            return resp["items"]
        return []

    def get_tab_feed(self, module_key: str, offset: int = 0, clean: bool = True) -> list:
        """
        Ambil feed drama dari endpoint /homepage/v2/tab/feed (real app pagination).
        
        Args:
            module_key: Module key kategori (e.g. 1036=Populer, 1039=Perempuan, 1040=New, 1041=Laki-laki, 1065=Dubbing, 2204=Anime)
            offset: Item offset (0, 10, 20, ...)
            clean: Jika True, hapus item header/card navigasi (seperti card Top/ranking)
            
        Returns:
            List drama items
        """
        payload = {
            "next": f"last_quality=0&offset={offset}&position_index=10000&timestamp=",
            "user_new_theater": False,
            "module_key": str(module_key)
        }
        resp = self._request("POST", "/frv2-api/homepage/v2/tab/feed", json=payload)
        if not resp or "items" not in resp:
            return []
        
        items = resp["items"]
        if clean:
            items = [
                it for it in items
                if not (
                    it.get("item_type") == "card" or
                    (not it.get("key") and it.get("title") == "Top") or
                    (it.get("module_card") is not None and isinstance(it.get("module_card"), dict) and "tab_list" in it.get("module_card", {})) or
                    (not it.get("key") and it.get("module_card") is not None)
                )
            ]
        return items

    def login_anonymous(self, device_id: str = None, device_name: str = "Xiaomi Redmi 5 Plus") -> bool:
        """
        Melakukan anonymous (guest) login otomatis ke server FreeReels.
        Meng-generate device_id unik, menghitung sign MD5, dan menyetel credential.
        Sistem menjadi fully independent tanpa memerlukan HP fisik.
        
        Returns: True jika login berhasil, False jika gagal.
        """
        import uuid
        import hashlib
        
        if not device_id:
            device_id = uuid.uuid4().hex[:16]
        
        self.device_id = device_id
        
        # Secret prefix untuk anonymous login sign (tanpa '&')
        LOGIN_SECRET_PREFIX = "8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv"
        raw = f"{LOGIN_SECRET_PREFIX}{device_id}"
        sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
        
        payload = {
            "device_id": device_id,
            "device_name": device_name,
            "sign": sign,
        }
        
        url = urljoin(self.base_url, "/frv2-api/anonymous/login")
        
        # Simpan header asli dan pastikan device-id sesuai
        headers = dict(self.session.headers)
        headers["device-id"] = device_id
        # /anonymous/login TIDAK boleh ada Authorization header
        headers.pop("Authorization", None)
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") in (0, 200):
                    info = data.get("data", {})
                    oauth_token = info.get("auth_key")
                    oauth_secret = info.get("auth_secret")
                    user_id = str(info.get("user_id", ""))
                    name = info.get("name", "Guest")
                    
                    self.set_oauth_credentials(oauth_token, oauth_secret, user_id)
                    self.session.headers["device-id"] = device_id
                    print(f"[*] Anonymous login successful!")
                    print(f"    User:    {name} (ID: {user_id})")
                    print(f"    Token:   {oauth_token[:10]}...{oauth_token[-5:]}")
                    return True
                else:
                    print(f"[!] Anonymous login API error: {data.get('message')}")
            else:
                print(f"[!] Anonymous login HTTP error: {resp.status_code}")
        except Exception as e:
            print(f"[!] Anonymous login failed: {e}")
        
        return False

        
    def set_oauth_credentials(self, oauth_token: str, oauth_secret: str, user_id: str = None):
        """
        Set OAuth credentials for authenticated requests.
        
        Args:
            oauth_token: The OAuth access token
            oauth_secret: The OAuth secret used for signing
            user_id: The User ID (optional)
        """
        self.signer.update(oauth_token=oauth_token, oauth_secret=oauth_secret)
        self.user_id = user_id
        print(f"[*] OAuth credentials set for user: {user_id or 'Unknown'}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request dengan error handling dan OAuth Signature"""
        url = urljoin(self.base_url, endpoint)
        
        # Auto-generate device ID jika belum ada
        if "X-Device-Id" not in self.session.headers:
            import uuid
            device_id = str(uuid.uuid4())
            self.session.headers.update({"X-Device-Id": device_id})
        
        # Inject OAuth Signature Header if configured
        if self.signer.is_configured():
            try:
                auth_header = self.signer.get_header()
                kwargs["headers"] = kwargs.get("headers", {})
                kwargs["headers"]["Authorization"] = auth_header
            except Exception as e:
                print(f"[!] Signature Error: {e}")
        
        try:
            print(f"\n[*] Request: {method} {url}")
            if self.signer.is_configured():
                print(f"    Auth: {kwargs.get('headers', {}).get('Authorization', '')[:40]}...")
            
            response = self.session.request(method, url, **kwargs)
            
            # Print response info for debugging
            print(f"    Status: {response.status_code}")
            
            response.raise_for_status()
            
            # Check if response is encrypted (header x-decry=1 or non-JSON body)
            x_decry = response.headers.get("x-decry", "0")
            body_text = response.text
            
            if x_decry == "1" or (not body_text.startswith("{") and not body_text.startswith("[")):
                print(f"    [*] Encrypted response detected (x-decry={x_decry}). Attempting native decrypt...")
                decrypted = decrypt_native_response(body_text.strip())
                if decrypted:
                    print("    [OK] Decryption successful!")
                    data = json.loads(decrypted)
                else:
                    print("    [!] Decryption failed. Trying raw JSON parse...")
                    data = response.json()
            else:
                data = response.json()
            
            # Check response code
            if data.get("code", 0) in (0, 200):
                return data.get("data")
            else:
                error_msg = data.get("message", "Unknown error")
                error_code = data.get("code", -1)
                print(f"[!] API Error {error_code}: {error_msg}")
                
                # Hint untuk authentication
                if error_code == 401 or "auth" in error_msg.lower():
                    print("    [*] Hint: Perlu login! Pilih menu [7] User Profile -> Login")
                elif error_code == 404:
                    print("    [*] Hint: Endpoint mungkin tidak ada atau URL salah")
                elif error_code == 403:
                    print("    [*] Hint: Access denied, mungkin perlu VIP atau region lock")
                
                return None

                
        except requests.exceptions.HTTPError as e:
            print(f"[!] HTTP Error: {e}")
            if e.response is not None:
                print(f"    Status Code: {e.response.status_code}")
                print(f"    Response: {e.response.text[:200]}")
                
                # Hints based on status code
                if e.response.status_code == 404:
                    print("    [*] Endpoint tidak ditemukan. API mungkin menggunakan path berbeda.")
                elif e.response.status_code == 401:
                    print("    [*] Perlu authentication! Login dulu di menu User Profile.")
                elif e.response.status_code == 403:
                    print("    [*] Access forbidden. Mungkin perlu token/headers tambahan.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[!] Request Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[!] JSON Decode Error: {e}")
            # Try to print raw response
            if 'response' in locals():
                print(f"    Raw response: {response.text[:200]}")
            return None
    
    # ========================================
    # THEATER/FEED ENDPOINTS
    # ========================================
    
    def get_theater_feed(self, tab: str = "recommend", page: int = 1) -> Optional[Dict]:
        """Get main theater feed"""
        return self._request("GET", "/v1/theater/feed", params={
            "tab": tab,
            "page": page
        })
    
    def get_recommend(self, source: str = "home") -> Optional[Dict]:
        """Get recommended content"""
        return self._request("GET", "/v1/theater/recommend", params={
            "source": source
        })
    
    def get_hot_list(self, content_type: str = "drama") -> Optional[Dict]:
        """Get hot/trending content"""
        return self._request("GET", "/v1/theater/hot_list", params={
            "type": content_type
        })
    
    def get_coming_soon(self, date_from: str = None, date_to: str = None) -> Optional[Dict]:
        """Get coming soon content"""
        from datetime import datetime, timedelta
        if not date_from:
            date_from = datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        return self._request("GET", "/v1/coming_soon/list", params={
            "date_from": date_from,
            "date_to": date_to
        })
    
    # ========================================
    # VIDEO/CONTENT ENDPOINTS
    # ========================================
    
    def get_video_detail(self, series_id: str, episode_id: str = None, scene: str = None) -> Optional[Dict]:
        """Get video/detail drama. API uses /frv2-api/drama/info_v2 with scene parameter."""
        params = {"series_id": series_id}
        # API param is 'scene' (episode index), not 'episode_id' (episode UUID)
        if scene:
            params["scene"] = scene
        elif episode_id:
            # Fallback: if only episode_id provided, try as scene
            params["scene"] = episode_id
        return self._request("GET", "/frv2-api/drama/info_v2", params=params)
    
    def get_content_rating(self, content_id: str) -> Optional[Dict]:
        """Get content rating/tags"""
        return self._request("GET", "/v1/content/rating", params={
            "content_id": content_id
        })
    
    def unlock_episode(self, episode_id: str, payment_type: str = "coin", 
                       coin_amount: int = 10) -> Optional[Dict]:
        """Unlock episode"""
        return self._request("POST", "/v1/video/unlock", json={
            "episode_id": episode_id,
            "payment_type": payment_type,
            "coin_amount": coin_amount
        })
    
    def get_subtitle_list(self, video_id: str, lang: str = "en") -> Optional[Dict]:
        """Get subtitle list"""
        return self._request("GET", "/v1/subtitle/list", params={
            "video_id": video_id,
            "lang": lang
        })
    
    # ========================================
    # SEARCH ENDPOINTS
    # ========================================
    
    def search(self, query: str, content_type: str = "drama", page: int = 1) -> Optional[Dict]:
        """Search content"""
        return self._request("GET", "/v1/search/query", params={
            "q": query,
            "type": content_type,
            "page": page
        })
    
    # ========================================
    # ACTOR ENDPOINTS
    # ========================================
    
    def get_popular_actors(self, page: int = 1) -> Optional[Dict]:
        """Get popular actors"""
        return self._request("GET", "/v1/actor/popular", params={
            "page": page
        })
    
    # ========================================
    # MYLIST ENDPOINTS
    # ========================================
    
    def get_mylist(self, user_id: str = None, list_type: str = "drama") -> Optional[Dict]:
        """Get user's mylist"""
        params = {"type": list_type}
        if user_id or self.user_id:
            params["user_id"] = user_id or self.user_id
        return self._request("GET", "/v1/mylist", params=params)
    
    def add_to_mylist(self, content_id: str, content_type: str = "drama") -> Optional[Dict]:
        """Add content to mylist"""
        return self._request("POST", "/v1/mylist/add", json={
            "content_id": content_id,
            "content_type": content_type
        })
    
    def remove_from_mylist(self, content_id: str) -> Optional[Dict]:
        """Remove content from mylist"""
        return self._request("DELETE", f"/v1/mylist/remove", params={
            "content_id": content_id
        })
    
    # ========================================
    # COMMENT ENDPOINTS
    # ========================================
    
    def get_comments(self, content_id: str, page: int = 1, size: int = 20) -> Optional[Dict]:
        """Get comments"""
        return self._request("GET", "/v1/comment/list", params={
            "content_id": content_id,
            "page": page,
            "size": size
        })
    
    def add_comment(self, content_id: str, comment: str, rating: int = 5) -> Optional[Dict]:
        """Add comment"""
        return self._request("POST", "/v1/comment/add", json={
            "content_id": content_id,
            "comment": comment,
            "rating": rating
        })
    
    # ========================================
    # USER/WALLET ENDPOINTS
    # ========================================
    
    def login(self, phone: str, otp: str, country_code: str = "ID") -> Optional[Dict]:
        """Login with phone OTP"""
        return self._request("POST", "/v1/user/login", json={
            "phone": phone,
            "otp": otp,
            "country_code": country_code
        })
    
    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        return self._request("GET", "/v1/user/profile")
    
    def get_wallet_balance(self, user_id: str = None) -> Optional[Dict]:
        """Get wallet balance"""
        data = {"user_id": user_id or self.user_id, "platform": "android"}
        return self._request("POST", "/v1/user/wallet/balance", json=data)
    
    def get_vip_status(self) -> Optional[Dict]:
        """Get VIP status"""
        return self._request("GET", "/v1/user/vip/status")
    
    # ========================================
    # REWARD ENDPOINTS
    # ========================================
    
    def daily_checkin(self, date: str = None) -> Optional[Dict]:
        """Daily check-in reward"""
        from datetime import datetime
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        return self._request("POST", "/v1/reward/checkin", json={
            "date": date
        })
    
    def get_daily_tasks(self) -> Optional[Dict]:
        """Get daily tasks"""
        return self._request("GET", "/v1/reward/tasks/daily")
    
    # ========================================
    # NEW ENDPOINTS (dari log Frida)
    # ========================================
    
    def get_content_message_unread(self):
        """Get unread messages"""
        return self._request("GET", "/content/message/unread")
    
    def get_popup_banner_list(self, scene_type: int = 14):
        """Get popup banner list"""
        return self._request("POST", "/popup/banner/list", json={
            "scene_type": scene_type
        })
    
    def get_wallet_my(self):
        """Get user wallet"""
        return self._request("GET", "/wallet/my")
    
    def get_drama_follow_list(self, series_type: int = 1, next_page: str = ""):
        """Get drama follow list"""
        return self._request("GET", "/drama/v3/follow_list", params={
            "next": next_page,
            "series_type": series_type
        })
    
    def user_risk_check(self):
        """User risk check"""
        return self._request("GET", "/user/risk/check")
    
    # ========================================
    # CONFIG ENDPOINTS
    # ========================================
    
    def get_app_version(self, version: str = "2.2.00") -> Optional[Dict]:
        """Check app version config"""
        return self._request("GET", "/v1/config/app_version", params={
            "version": version
        })
    
    def get_home_banner(self) -> Optional[Dict]:
        """Get home banner"""
        return self._request("GET", "/v1/banner/home")


# ============================================
# INTERACTIVE MENU CLASS
# ============================================

class InteractiveMenu:
    """Interactive menu untuk browse drama"""
    
    def __init__(self):
        self.client = FreeReelsClient()
        self.current_drama: Optional[Dict] = None
        self.current_episodes: List[Dict] = []
        self.selected_episode: Optional[Dict] = None
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Print formatted header"""
        self.clear_screen()
        print("=" * 60)
        print(f"  {title}")
        print("=" * 60)
        print()
    
    def print_menu(self, options: List[str]):
        """Print menu options"""
        for i, option in enumerate(options, 1):
            print(f"  [{i}] {option}")
        print(f"  [0] Back/Exit")
        print()
    
    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input"""
        while True:
            value = input(f"> {prompt}: ").strip()
            if value or not required:
                return value
            print("  Input tidak boleh kosong!")
    
    def get_choice(self, max_choice: int) -> int:
        """Get menu choice"""
        while True:
            try:
                choice = int(input("> Pilihan: "))
                if 0 <= choice <= max_choice:
                    return choice
                print(f"  Pilih angka antara 0-{max_choice}")
            except ValueError:
                print("  Input harus angka!")
    
    # ========================================
    # MAIN MENU
    # ========================================
    
    def main_menu(self):
        """Main menu"""
        while True:
            self.print_header("FREEREELS - DRAMA BROWSER")
            print("  Pilih menu:")
            print()
            self.print_menu([
                "📺 Theater Feed (Recommend)",
                "🔥 Hot/Trending Drama",
                "📅 Coming Soon",
                "🔍 Search Drama",
                "🎭 Popular Actors",
                "📋 My Watchlist",
                "👤 User Profile",
                "🎁 Daily Rewards"
            ])
            
            choice = self.get_choice(8)
            
            if choice == 0:
                if confirm("Keluar dari aplikasi?"):
                    sys.exit(0)
            elif choice == 1:
                self.theater_feed_menu()
            elif choice == 2:
                self.hot_list_menu()
            elif choice == 3:
                self.coming_soon_menu()
            elif choice == 4:
                self.search_menu()
            elif choice == 5:
                self.actors_menu()
            elif choice == 6:
                self.mylist_menu()
            elif choice == 7:
                self.profile_menu()
            elif choice == 8:
                self.rewards_menu()
    
    # ========================================
    # DRAMA LIST DISPLAY
    # ========================================
    
    def display_drama_list(self, dramas: List[Dict], title: str = "Drama List"):
        """Display list of dramas"""
        if not dramas:
            print("  ❌ Tidak ada data")
            input("  Tekan Enter untuk lanjut...")
            return
        
        self.print_header(title)
        
        for i, drama in enumerate(dramas, 1):
            drama_id = drama.get("id", drama.get("series_id", "N/A"))
            drama_title = drama.get("title", drama.get("series_title", "No Title"))
            episode_count = drama.get("episode_count", drama.get("total_episodes", "?"))
            rating = drama.get("rating", drama.get("score", "-"))
            thumbnail = drama.get("thumbnail", drama.get("cover_image", ""))
            
            print(f"  [{i}] {drama_title}")
            print(f"      ID: {drama_id}")
            print(f"      Episodes: {episode_count} | Rating: {rating}")
            if thumbnail:
                print(f"      Thumbnail: {thumbnail[:50]}...")
            print()
        
        # Select drama
        max_choice = len(dramas)
        self.print_menu([f"Select Drama (1-{max_choice})"])
        
        choice = self.get_choice(max_choice)
        if choice > 0:
            self.current_drama = dramas[choice - 1]
            self.drama_detail_menu()
    
    # ========================================
    # THEATER FEED MENU
    # ========================================
    
    def theater_feed_menu(self):
        """Theater feed menu"""
        tabs = ["recommend", "picks_for_you", "popular_choice_hybrid"]
        
        self.print_header("THEATER FEED")
        print("  Pilih tab:")
        for i, tab in enumerate(tabs, 1):
            print(f"  [{i}] {tab.replace('_', ' ').title()}")
        
        tab_choice = self.get_choice(len(tabs))
        if tab_choice == 0:
            return
        
        selected_tab = tabs[tab_choice - 1]
        
        print(f"\n[*] Loading feed: {selected_tab}...")
        result = self.client.get_theater_feed(tab=selected_tab, page=1)
        
        if result:
            # Extract drama list from response
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, f"Theater Feed - {selected_tab}")
        else:
            print("  ❌ Gagal mengambil data")
            input("  Tekan Enter untuk lanjut...")
    
    def hot_list_menu(self):
        """Hot list menu"""
        print("\n[*] Loading hot list...")
        result = self.client.get_hot_list(content_type="drama")
        
        if result:
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, "🔥 Hot/Trending Drama")
        else:
            print("  ❌ Gagal mengambil data")
            input("  Tekan Enter untuk lanjut...")
    
    def coming_soon_menu(self):
        """Coming soon menu"""
        print("\n[*] Loading coming soon...")
        result = self.client.get_coming_soon()
        
        if result:
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, "📅 Coming Soon")
        else:
            print("  ❌ Gagal mengambil data")
            input("  Tekan Enter untuk lanjut...")
    
    def search_menu(self):
        """Search menu"""
        query = self.get_input("Masukkan keyword pencarian")
        
        print(f"\n[*] Searching: {query}...")
        result = self.client.search(query=query, content_type="drama", page=1)
        
        if result:
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, f"🔍 Search Results: {query}")
        else:
            print("  ❌ Gagal mengambil data")
            input("  Tekan Enter untuk lanjut...")
    
    def actors_menu(self):
        """Popular actors menu"""
        print("\n[*] Loading popular actors...")
        result = self.client.get_popular_actors(page=1)
        
        if result:
            self._display_actors(result)
        else:
            print("  ❌ Gagal mengambil data")
            input("  Tekan Enter untuk lanjut...")
    
    def _display_actors(self, data: Dict):
        """Display actors list"""
        actors = data.get("list", data.get("actors", []))
        if not actors:
            print("  Tidak ada data")
            input("  Tekan Enter untuk lanjut...")
            return
        
        self.print_header("🎭 POPULAR ACTORS")
        
        for i, actor in enumerate(actors, 1):
            name = actor.get("name", "Unknown")
            popularity = actor.get("popularity", actor.get("rank", "-"))
            print(f"  [{i}] {name}")
            print(f"      Popularity: {popularity}")
            print()
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # DRAMA DETAIL MENU
    # ========================================
    
    def drama_detail_menu(self):
        """Drama detail menu"""
        if not self.current_drama:
            print("  ❌ No drama selected")
            input("  Tekan Enter untuk lanjut...")
            return
        
        drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
        
        self.print_header("📺 DRAMA DETAIL")
        
        # Get full detail
        print("[*] Loading drama detail...")
        detail = self.client.get_video_detail(series_id=drama_id)
        
        if detail:
            self._display_drama_detail(detail)
            self.current_drama.update(detail)  # Merge data
        else:
            self._display_drama_detail(self.current_drama)
        
        # Menu options
        self.print_menu([
            "📋 View Episodes",
            "▶️ Play First Episode",
            "💬 View Comments",
            "❤️ Add to MyList",
            "🔍 Search Similar"
        ])
        
        choice = self.get_choice(5)
        
        if choice == 1:
            self.episodes_menu()
        elif choice == 2:
            self.play_first_episode()
        elif choice == 3:
            self.comments_menu(drama_id)
        elif choice == 4:
            self._add_to_mylist(drama_id)
        elif choice == 5:
            title = self.current_drama.get("title", "")
            if title:
                keywords = title.split()[:2]
                search_query = " ".join(keywords)
                self.search_with_query(search_query)
    
    def _display_drama_detail(self, detail: Dict):
        """Display drama detail information"""
        print()
        print("  " + "=" * 50)
        
        title = detail.get("title", detail.get("series_title", "No Title"))
        print(f"  📺 {title}")
        print()
        
        # Basic info
        print(f"  📝 Series ID: {detail.get('id', detail.get('series_id', 'N/A'))}")
        print(f"  🎬 Type: {detail.get('type', detail.get('content_type', 'Drama'))}")
        print(f"  📊 Rating: {detail.get('rating', detail.get('score', 'N/A'))}")
        print(f"  📀 Total Episodes: {detail.get('episode_count', detail.get('total_episodes', 'N/A'))}")
        print(f"  📅 Status: {detail.get('status', detail.get('publish_status', 'N/A'))}")
        print(f"  🌟 Cast: {detail.get('cast', detail.get('actors', 'N/A'))}")
        print()
        
        # Synopsis
        synopsis = detail.get("synopsis", detail.get("description", detail.get("summary", "")))
        if synopsis:
            print(f"  📖 Synopsis:")
            # Wrap text
            words = synopsis.split()
            lines = []
            current_line = "      "
            for word in words:
                if len(current_line) + len(word) > 60:
                    lines.append(current_line)
                    current_line = "      " + word + " "
                else:
                    current_line += word + " "
            lines.append(current_line)
            for line in lines[:10]:  # Max 10 lines
                print(line)
            if len(lines) > 10:
                print("      ...")
            print()
        
        # Additional info
        if "genres" in detail or "tags" in detail:
            genres = detail.get("genres", detail.get("tags", []))
            if isinstance(genres, list):
                print(f"  🏷️  Genres: {', '.join(genres)}")
            print()
        
        # Thumbnail/cover
        thumbnail = detail.get("thumbnail", detail.get("cover_image", detail.get("banner", "")))
        if thumbnail:
            print(f"  🖼️  Thumbnail: {thumbnail}")
        print("  " + "=" * 50)
        print()
    
    # ========================================
    # EPISODES MENU
    # ========================================
    
    def episodes_menu(self):
        """Episodes list menu"""
        if not self.current_drama:
            return
        
        drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
        
        self.print_header("📀 EPISODES LIST")
        
        # Get episodes (might be in detail response)
        episodes = self.current_drama.get("episodes", [])
        
        if not episodes:
            # Try to fetch episodes
            print("[*] Loading episodes...")
            detail = self.client.get_video_detail(series_id=drama_id)
            if detail:
                episodes = detail.get("episodes", [])
                self.current_drama["episodes"] = episodes
        
        if not episodes:
            print("  ❌ No episodes found")
            input("  Tekan Enter untuk lanjut...")
            return
        
        self.current_episodes = episodes
        
        # Display episodes
        for i, episode in enumerate(episodes, 1):
            ep_id = episode.get("id", episode.get("episode_id"))
            ep_num = episode.get("number", episode.get("episode_num", i))
            ep_title = episode.get("title", f"Episode {ep_num}")
            is_free = episode.get("is_free", episode.get("free", False))
            is_locked = episode.get("is_locked", episode.get("locked", not is_free))
            
            status = "🔓 FREE" if is_free else "🔒 LOCKED"
            print(f"  [{i}] Episode {ep_num}: {ep_title} {status}")
        
        print()
        self.print_menu([f"Select Episode (1-{len(episodes)})"])
        
        choice = self.get_choice(len(episodes))
        if choice > 0:
            self.selected_episode = episodes[choice - 1]
            self.episode_detail_menu()
    
    def episode_detail_menu(self):
        """Episode detail menu"""
        if not self.selected_episode:
            return
        
        self.print_header("▶️ EPISODE DETAIL")
        
        ep_id = self.selected_episode.get("id", self.selected_episode.get("episode_id"))
        ep_num = self.selected_episode.get("number", self.selected_episode.get("episode_num", "?"))
        ep_title = self.selected_episode.get("title", f"Episode {ep_num}")
        
        print(f"  📀 {ep_title}")
        print(f"  ID: {ep_id}")
        print()
        
        # Check if free or locked
        is_free = self.selected_episode.get("is_free", True)
        is_locked = not is_free
        
        if is_locked:
            print("  🔒 Episode LOCKED")
            print("     Need coins or VIP to unlock")
            print()
        
        # Menu
        if is_free:
            self.print_menu([
                "▶️ PLAY Episode",
                "📥 Get Video URL",
                "💬 View Comments",
                "📊 Get Subtitles"
            ])
            
            choice = self.get_choice(4)
            
            if choice == 1:
                self.play_episode(ep_id)
            elif choice == 2:
                self.get_video_url(ep_id)
            elif choice == 3:
                drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
                self.comments_menu(drama_id)
            elif choice == 4:
                self.subtitles_menu(ep_id)
        else:
            self.print_menu([
                "🔓 Unlock Episode (Simulated)",
                "💬 View Comments"
            ])
            
            choice = self.get_choice(2)
            
            if choice == 1:
                self.unlock_episode(ep_id)
            elif choice == 2:
                drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
                self.comments_menu(drama_id)
    
    def play_first_episode(self):
        """Play first episode"""
        if not self.current_drama:
            return
        
        episodes = self.current_drama.get("episodes", [])
        if episodes:
            self.selected_episode = episodes[0]
            ep_id = episodes[0].get("id", episodes[0].get("episode_id"))
            self.play_episode(ep_id)
        else:
            print("  ❌ No episodes available")
            input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # PLAYBACK
    # ========================================
    
    def play_episode(self, episode_id: str):
        """Play episode"""
        self.print_header("▶️ PLAYING EPISODE")
        
        print("[*] Getting video URL...")
        
        # Get video detail with episode_id
        drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
        detail = self.client.get_video_detail(series_id=drama_id, episode_id=episode_id)
        
        if detail and "video_url" in detail:
            video_url = detail["video_url"]
            self._play_video(video_url)
        else:
            # Try to construct URL from known patterns
            print("[*] Trying to construct video URL...")
            
            # Common video URL patterns from JADX analysis
            video_url = f"{VIDEO_BASE_URL}/vt/prod/{drama_id}/{episode_id}.m3u8"
            print(f"    Constructed URL: {video_url}")
            
            self._play_video(video_url)
    
    def get_video_url(self, episode_id: str):
        """Get and display video URL"""
        drama_id = self.current_drama.get("id", self.current_drama.get("series_id"))
        
        # Try to get from API
        detail = self.client.get_video_detail(series_id=drama_id, episode_id=episode_id)
        
        self.print_header("📥 VIDEO URL")
        
        if detail and "video_url" in detail:
            video_url = detail["video_url"]
            print(f"  Video URL: {video_url}")
            print()
            
            # Offer to open in browser
            if confirm("Buka URL di browser?"):
                webbrowser.open(video_url)
        else:
            # Construct URL
            video_url = f"{VIDEO_BASE_URL}/vt/prod/{drama_id}/{episode_id}.m3u8"
            print(f"  Constructed URL: {video_url}")
            print()
            print("  ⚠️  This is a constructed URL, may not work")
            print()
            
            if confirm("Coba buka di browser?"):
                webbrowser.open(video_url)
        
        input("  Tekan Enter untuk lanjut...")
    
    def _play_video(self, video_url: str):
        """Play video using external player"""
        print()
        print(f"  🎬 Video URL: {video_url}")
        print()
        print("  Choose player:")
        print("  [1] Open in Browser")
        print("  [2] Open with VLC")
        print("  [3] Open with MPC-HC")
        print("  [4] Copy URL to clipboard")
        print("  [0] Back")
        print()
        
        choice = self.get_choice(4)
        
        if choice == 1:
            print("  Opening in browser...")
            webbrowser.open(video_url)
        elif choice == 2:
            print("  Opening with VLC...")
            try:
                subprocess.Popen(["vlc", video_url])
            except FileNotFoundError:
                print("  ❌ VLC not found!")
        elif choice == 3:
            print("  Opening with MPC-HC...")
            try:
                subprocess.Popen(["mpc-hc", video_url])
            except FileNotFoundError:
                print("  ❌ MPC-HC not found!")
        elif choice == 4:
            # Copy to clipboard (simple way)
            import pyperclip
            pyperclip.copy(video_url)
            print("  ✅ URL copied to clipboard!")
        
        input("  Tekan Enter untuk lanjut...")
    
    def unlock_episode(self, episode_id: str):
        """Unlock episode (simulated)"""
        self.print_header("🔓 UNLOCK EPISODE")
        
        print("  Episode unlock requires:")
        print("  - Coins (in-app currency)")
        print("  - OR VIP subscription")
        print()
        print("  💰 Cost: ~10 coins per episode")
        print("  👑 VIP: Unlimited access")
        print()
        
        if confirm("Simulate unlock? (Won't actually work without auth)"):
            print("\n  [*] Sending unlock request...")
            result = self.client.unlock_episode(episode_id=episode_id)
            
            if result:
                print("  ✅ Episode unlocked!")
                self.selected_episode["is_locked"] = False
                self.selected_episode["is_free"] = True
            else:
                print("  ❌ Unlock failed (need authentication)")
                print("     Please login first")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # SUBTITLES
    # ========================================
    
    def subtitles_menu(self, episode_id: str):
        """Subtitles menu"""
        self.print_header("📊 SUBTITLES")
        
        print("[*] Getting subtitle list...")
        result = self.client.get_subtitle_list(video_id=episode_id, lang="en")
        
        if result:
            subtitles = result.get("list", result.get("subtitles", []))
            
            if subtitles:
                for i, sub in enumerate(subtitles, 1):
                    lang = sub.get("lang", sub.get("language", "Unknown"))
                    url = sub.get("url", sub.get("file", ""))
                    print(f"  [{i}] {lang}")
                    print(f"      URL: {url}")
                    print()
                
                # Select subtitle
                choice = self.get_choice(len(subtitles))
                if choice > 0:
                    sub_url = subtitles[choice - 1].get("url")
                    if sub_url:
                        print(f"\n  Opening subtitle: {sub_url}")
                        if confirm("Buka di browser?"):
                            webbrowser.open(sub_url)
            else:
                print("  No subtitles available")
        else:
            print("  ❌ Failed to get subtitles")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # COMMENTS
    # ========================================
    
    def comments_menu(self, content_id: str):
        """Comments menu"""
        self.print_header("💬 COMMENTS")
        
        print("[*] Loading comments...")
        result = self.client.get_comments(content_id=content_id, page=1, size=20)
        
        if result:
            comments = result.get("list", result.get("comments", []))
            
            if comments:
                for i, comment in enumerate(comments, 1):
                    user = comment.get("user", comment.get("username", "Anonymous"))
                    text = comment.get("comment", comment.get("content", ""))
                    rating = comment.get("rating", "")
                    
                    print(f"  [{i}] {user}" + (f" ⭐{rating}" if rating else ""))
                    print(f"      {text[:80]}...")
                    print()
            else:
                print("  No comments yet")
        else:
            print("  ❌ Failed to load comments")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # MYLIST
    # ========================================
    
    def mylist_menu(self):
        """My watchlist menu"""
        self.print_header("📋 MY WATCHLIST")
        
        print("  ⚠️  Requires authentication")
        print()
        
        if not self.client.auth_token:
            print("  Not authenticated!")
            print()
            if confirm("Login sekarang?"):
                self.login_menu()
            return
        
        result = self.client.get_mylist()
        
        if result:
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, "📋 My Watchlist")
        else:
            print("  ❌ Failed to load mylist")
            input("  Tekan Enter untuk lanjut...")
    
    def _add_to_mylist(self, content_id: str):
        """Add drama to mylist"""
        if not self.client.auth_token:
            print("  ❌ Need authentication")
            print("     Please login first")
            input("  Tekan Enter untuk lanjut...")
            return
        
        print("\n[*] Adding to mylist...")
        result = self.client.add_to_mylist(content_id=content_id)
        
        if result:
            print("  ✅ Added to mylist!")
        else:
            print("  ❌ Failed to add")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # PROFILE & AUTH
    # ========================================
    
    def profile_menu(self):
        """User profile menu"""
        self.print_header("👤 USER PROFILE")
        
        if not self.client.auth_token:
            print("  Not authenticated")
            print()
            self.print_menu(["Login", "Input Manual Token", "Load from Frida Log"])
            
            choice = self.get_choice(3)
            if choice == 1:
                self.login_menu()
            elif choice == 2:
                self.manual_token_menu()
            elif choice == 3:
                self.load_from_frida_log()
            return
        
        # Get profile
        print("[*] Loading profile...")
        profile = self.client.get_profile()
        
        if profile:
            print()
            print(f"  👤 Username: {profile.get('username', 'N/A')}")
            print(f"  📧 Email: {profile.get('email', 'N/A')}")
            print(f"  💰 Coins: {profile.get('coins', profile.get('balance', '0'))}")
            print(f"  👑 VIP: {profile.get('vip_status', profile.get('is_vip', 'No'))}")
            print()
        else:
            print("  Failed to load profile")
        
        self.print_menu(["Logout", "View Current Token"])
        
        choice = self.get_choice(2)
        if choice == 1:
            self.client.set_auth("")
            print("  Logged out")
        elif choice == 2:
            if self.client.auth_token:
                print(f"\n  Token: {self.client.auth_token}")
                print(f"  User ID: {self.client.user_id}")
                input("  Tekan Enter untuk lanjut...")
        
        input("  Tekan Enter untuk lanjut...")
    
    def manual_token_menu(self):
        """Input manual token"""
        self.print_header("🔑 INPUT MANUAL TOKEN")
        
        print("  Masukkan Bearer Token dari:")
        print("  - Frida log output")
        print("  - Burp Suite capture")
        print("  - Aplikasi Android (root required)")
        print()
        
        token = self.get_input("Bearer Token", required=False)
        if not token:
            print("  Token kosong, batal")
            input("  Tekan Enter untuk lanjut...")
            return
        
        user_id = self.get_input("User ID (optional)", required=False)
        
        self.client.set_auth(token, user_id if user_id else None)
        print("  ✅ Token saved!")
        print()
        print("  Sekarang bisa akses fitur yang perlu authentication")
        
        input("  Tekan Enter untuk lanjut...")
    
    def load_from_frida_log(self):
        """Load token dari frida_output.log"""
        self.print_header("📝 LOAD TOKEN DARI FRIDA LOG")
        
        log_file = "frida_output.log"
        
        if not os.path.exists(log_file):
            print(f"  ❌ File {log_file} tidak ditemukan")
            print("     Jalankan frida_hook.js dulu untuk capture traffic")
            input("  Tekan Enter untuk lanjut...")
            return
        
        print(f"  [*] Reading {log_file}...")
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Cari Bearer token
            import re
            bearer_pattern = r'Bearer\s+([A-Za-z0-9\-_\.]+)'
            tokens = re.findall(bearer_pattern, content)
            
            if not tokens:
                print("  ❌ Tidak menemukan Bearer token di log")
                input("  Tekan Enter untuk lanjut...")
                return
            
            # Remove duplicates
            unique_tokens = list(set(tokens))
            
            print(f"  ✅ Ditemukan {len(unique_tokens)} token(s)")
            print()
            
            # Show tokens
            for i, token in enumerate(unique_tokens, 1):
                print(f"  [{i}] {token[:50]}...")
            
            print()
            print(f"  Pilih token (1-{len(unique_tokens)}):")
            
            try:
                choice = int(input("> Pilihan: "))
                if 1 <= choice <= len(unique_tokens):
                    selected_token = tokens[choice - 1]
                    
                    # Try to find user_id
                    user_id_pattern = r'"user_id"\s*:\s*"(\d+)"'
                    user_ids = re.findall(user_id_pattern, content)
                    user_id = user_ids[0] if user_ids else None
                    
                    self.client.set_auth(selected_token, user_id)
                    
                    print("  ✅ Token loaded!")
                    if user_id:
                        print(f"  User ID: {user_id}")
                else:
                    print("  Pilihan tidak valid")
            except ValueError:
                print("  Input harus angka")
            
        except Exception as e:
            print(f"  ❌ Error reading log: {e}")
        
        input("  Tekan Enter untuk lanjut...")
    
    def login_menu(self):
        """Login menu"""
        self.print_header("🔐 LOGIN")
        
        print("  Login dengan Phone OTP")
        print()
        
        phone = self.get_input("Phone number (e.g., 628123456789)")
        otp = self.get_input("OTP code")
        
        print("\n[*] Logging in...")
        result = self.client.login(phone=phone, otp=otp)
        
        if result:
            token = result.get("token", result.get("access_token", ""))
            user_id = result.get("user_id", result.get("uid", ""))
            
            if token:
                self.client.set_auth(token, user_id)
                print("  ✅ Login successful!")
            else:
                print("  ❌ Login failed (no token)")
        else:
            print("  ❌ Login failed")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # REWARDS
    # ========================================
    
    def rewards_menu(self):
        """Daily rewards menu"""
        self.print_header("🎁 DAILY REWARDS")
        
        if not self.client.auth_token:
            print("  ⚠️  Requires authentication")
            print()
            if confirm("Login sekarang?"):
                self.login_menu()
            return
        
        self.print_menu([
            "📅 Daily Check-in",
            "📋 View Daily Tasks"
        ])
        
        choice = self.get_choice(2)
        
        if choice == 1:
            print("\n[*] Doing daily check-in...")
            result = self.client.daily_checkin()
            
            if result:
                reward = result.get("reward", result.get("coins", 0))
                print(f"  ✅ Check-in successful!")
                print(f"  🎁 Reward: {reward} coins")
            else:
                print("  ❌ Check-in failed (may already done today)")
        
        elif choice == 2:
            print("\n[*] Loading daily tasks...")
            result = self.client.get_daily_tasks()
            
            if result:
                tasks = result.get("tasks", result.get("list", []))
                for task in tasks:
                    title = task.get("title", "Unknown task")
                    reward = task.get("reward", 0)
                    status = task.get("status", "pending")
                    print(f"  • {title} - {reward} coins [{status}]")
            else:
                print("  ❌ Failed to load tasks")
        
        input("  Tekan Enter untuk lanjut...")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _extract_dramas_from_feed(self, data: Dict) -> List[Dict]:
        """Extract drama list from feed response"""
        # Try common response structures
        dramas = (
            data.get("list", []) or
            data.get("items", []) or
            data.get("data", []) or
            data.get("series", []) or
            data.get("dramas", [])
        )
        
        # Handle nested structure
        if not dramas and "modules" in data:
            modules = data["modules"]
            for module in modules:
                if "list" in module:
                    dramas = module["list"]
                    break
        
        return dramas
    
    def search_with_query(self, query: str):
        """Search with specific query"""
        print(f"\n[*] Searching: {query}...")
        result = self.client.search(query=query, content_type="drama", page=1)
        
        if result:
            dramas = self._extract_dramas_from_feed(result)
            self.display_drama_list(dramas, f"🔍 Search: {query}")


# ============================================
# HELPER FUNCTIONS
# ============================================

def confirm(prompt: str) -> bool:
    """Get yes/no confirmation"""
    while True:
        response = input(f"> {prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("  Input y atau n")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  FREEREELS - Interactive Drama Browser & Player")
    print("  Version: 1.0.0")
    print("=" * 60)
    print()
    print("[*] Starting application...")
    print()
    
    # Install required packages check
    try:
        import requests
        import pyperclip
    except ImportError as e:
        print(f"[!] Missing package: {e.name}")
        print("[*] Installing...")
        os.system("pip install requests pyperclip")
        print("[*] Please restart the application")
        sys.exit(1)
    
    # Start interactive menu
    menu = InteractiveMenu()
    menu.main_menu()
