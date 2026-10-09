"""
Production configuration for FreeReels API Client
"""

# API Configuration
API_BASE_URL = "https://apiv2.free-reels.com"
API_PREFIX = "/frv2-api"
TRACE_URL = "https://trace.free-reels.com"
VIDEO_BASE_URL = "https://video-v1.mydramawave.com"

# Authentication
LOGIN_SECRET = "8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv"
OAUTH_SECRET_SUFFIX = "&"

# AES Decryption Keys (extracted from libdwguard.so)
AES_KEY_FLAVOR_1 = "3sa9Kx7mQu3Ls8Wd"
AES_KEY_FLAVOR_2 = "79psatnvfgktswba"

# Default Headers
DEFAULT_HEADERS = {
    "User-Agent": "FreeReels/2.4.91 (Android 13; Redmi 5 Plus)",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "app-version": "2.4.91",
    "app-name": "com.freereels.app",
    "device": "android",
    "device-version": "33",
}

# Language Configuration (22 verified languages)
SUPPORTED_LANGUAGES = {
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
}

DEFAULT_LANGUAGE = "id-ID"
DEFAULT_COUNTRY = "ID"

# API Proxy Server
PROXY_HOST = os.getenv("HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PORT", 7406))

# Timeouts (seconds)
REQUEST_TIMEOUT = 15
LOGIN_TIMEOUT = 10
