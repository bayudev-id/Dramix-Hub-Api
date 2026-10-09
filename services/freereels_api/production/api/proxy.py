import time
import json
import uuid
import hashlib
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
import base64
from pathlib import Path
from Crypto.Cipher import AES

# ============================================================
# FastAPI App Setup
# ============================================================
app = FastAPI(
    title="FreeReels API Proxy",
    description="Proxy server untuk API FreeReels dengan playground testing",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Global State
# ============================================================
class APIState:
    def __init__(self):
        self.oauth_token = None
        self.oauth_secret = None
        self.user_id = None
        self.user_name = None
        self.device_id = uuid.uuid4().hex[:16]
        self.last_login = None
        self.token_expiry = None  # Token berlaku berapa lama (detik)
    
    def is_session_valid(self):
        """Check if current session token masih valid (tidak expired)"""
        if not self.oauth_token or not self.last_login or not self.token_expiry:
            return False
        elapsed = time.time() - self.last_login
        return elapsed < self.token_expiry

state = APIState()

# ============================================================
# Constants
# ============================================================
BASE_URL = "https://apiv2.free-reels.com"
API_PREFIX = "/frv2-api"
LOGIN_SECRET_PREFIX = "8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv"

AES_KEYS = {
    1: b"3sa9Kx7mQu3Ls8Wd",
    2: b"79psatnvfgktswba",
}

# ============================================================
# Pydantic Models
# ============================================================
class LoginResponse(BaseModel):
    code: int
    message: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    token_preview: Optional[str] = None

class APITestRequest(BaseModel):
    method: str
    endpoint: str
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None

class APITestResponse(BaseModel):
    code: int
    status: int
    time_ms: float
    endpoint: str
    response: Any

# ============================================================
# Helper Functions
# ============================================================
def unpad_pkcs7(data: bytes) -> bytes:
    if not data:
        return data
    pad_len = data[-1]
    if 1 <= pad_len <= 16 and data[-pad_len:] == bytes([pad_len]) * pad_len:
        return data[:-pad_len]
    return data

def decrypt_response(base64_cipher: str) -> Optional[str]:
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

def build_oauth_header(token: str, secret: str) -> str:
    sig = hashlib.md5(f"{LOGIN_SECRET_PREFIX}&{secret}".encode()).hexdigest()
    ts = str(int(time.time() * 1000))
    return f"oauth_signature={sig},oauth_token={token},ts={ts}"

def build_common_headers() -> Dict[str, str]:
    return {
        "User-Agent": "FreeReels/2.4.91 (Android 13)",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "app-name": "com.freereels.app",
        "app-version": "2.4.91",
        "device-id": state.device_id,
        "country": "ID",
        "language": "id-ID",
    }

# ============================================================
# Authentication
# ============================================================
@app.post("/api/auth/login", response_model=LoginResponse)
async def login():
    # Return existing session jika masih valid (reuse token)
    if state.is_session_valid():
        return LoginResponse(
            code=200,
            message="Reusing active session",
            user_id=state.user_id,
            user_name=state.user_name,
            token_preview=f"{state.oauth_token[:10]}...{state.oauth_token[-5:]}" if state.oauth_token else "",
        )
        
    try:
        sign = hashlib.md5(f"{LOGIN_SECRET_PREFIX}{state.device_id}".encode()).hexdigest()
        
        headers = build_common_headers()
        payload = {
            "device_id": state.device_id,
            "device_name": "API Testing Client",
            "sign": sign,
        }
        
        resp = requests.post(
            f"{BASE_URL}{API_PREFIX}/anonymous/login",
            headers=headers,
            json=payload,
            timeout=15,
        )
        
        data = resp.json()
        
        if data.get("code") in (0, 200):
            info = data.get("data", {})
            state.oauth_token = info.get("auth_key")
            state.oauth_secret = info.get("auth_secret")
            state.user_id = info.get("id")
            state.user_name = info.get("name", "Guest")
            state.last_login = time.time()
            state.token_expiry = 3600  # Token valid 1 jam
            
            return LoginResponse(
                code=200,
                message="Login successful",
                user_id=state.user_id,
                user_name=state.user_name,
                token_preview=f"{state.oauth_token[:10]}...{state.oauth_token[-5:]}" if state.oauth_token else None,
            )
        else:
            return LoginResponse(
                code=400,
                message=data.get("message", "Login failed"),
            )
    except Exception as e:
        return LoginResponse(code=500, message=str(e))

@app.get("/api/auth/status")
async def auth_status():
    return {
        "authenticated": bool(state.oauth_token),
        "user_id": state.user_id,
        "user_name": state.user_name,
        "device_id": state.device_id,
        "last_login": state.last_login,
        "token_preview": f"{state.oauth_token[:10]}...{state.oauth_token[-5:]}" if state.oauth_token else None,
    }

@app.get("/api/tabs/complete")
async def tabs_complete():
    """
    Custom endpoint: Tab list lengkap dengan module_key + ranking tabs
    - Tabs reguler (kecuali 622 Segera Hadir): pakai module_key untuk /api/feed
    - Tab 622 Segera Hadir: tetap pakai tab_key untuk /tab/index (no pagination)
    - Ranking tabs baru: Daily, Weekly, Monthly, Annually
    """
    if not state.oauth_token:
        await login()
    
    if not state.oauth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Fetch original tab list
    url = BASE_URL + API_PREFIX + "/homepage/v2/tab/list"
    headers = build_common_headers()
    headers["Authorization"] = build_oauth_header(state.oauth_token, state.oauth_secret)
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp_text = resp.text
        
        x_decry = resp.headers.get("x-decry", "0")
        if x_decry == "1" and not resp_text.startswith("{"):
            decrypted = decrypt_response(resp_text.strip())
            if decrypted:
                resp_text = decrypted
        
        data = json.loads(resp_text)
        target_dict = data.get("data", data)
        
        if isinstance(target_dict, dict) and "list" in target_dict:
            # Mapping tab_key -> module_key untuk endpoint /api/feed
            tab_module_mapping = {
                "503": "1036",   # Populer
                "505": "1040",   # New
                "516": "1065",   # Dubbing
                "504": "1039",   # Perempuan
                "506": "1041",   # Laki-Laki
                "547": "2204",   # Anime
            }
            
            # Clean name mapping (user-friendly Indonesian names)
            clean_names = {
                "503": "Populer",
                "505": "New",
                "516": "Dubbing",
                "504": "Perempuan",
                "506": "Laki-Laki"
            }
            
            # Update tabs: replace tab_key with module_key, set clean names
            for tab in target_dict["list"]:
                tab_key = str(tab.get("tab_key"))
                if tab_key != "622" and tab_key in tab_module_mapping:
                    module_key = tab_module_mapping[tab_key]
                    
                    # Replace tab_key with module_key
                    tab.pop("tab_key", None)
                    tab["module_key"] = module_key
                    tab["feed_endpoint"] = "/api/feed"
                    
                    # Set clean Indonesian name
                    if tab_key in clean_names:
                        tab["name"] = clean_names[tab_key]
            
            # Inject anime tab (547) jika belum ada
            anime_exists = any(str(tab.get("module_key")) == "2204" for tab in target_dict["list"])
            if not anime_exists:
                anime_tab = {
                    "active": 0,
                    "business_name": "anime",
                    "name": "Anime",
                    "position_index": 10006,
                    "module_key": "2204",
                    "tab_type": 1,
                    "target_url": "",
                    "module_id": 2204,
                    "module_type": "recommend",
                    "feed_endpoint": "/api/feed",
                    "source": "custom_injected"
                }
                target_dict["list"].append(anime_tab)
            
            # Tambah ranking tabs (Daily, Weekly, Monthly, Annually)
            ranking_tabs = [
                {
                    "active": 0,
                    "business_name": "ranking_daily",
                    "name": "Harian",
                    "position_index": 10010,
                    "ranking_id": "daily",
                    "tab_type": 2,
                    "target_url": "",
                    "ranking_endpoint": "/api/ranking",
                    "ranking_period": "daily",
                    "source": "custom_ranking"
                },
                {
                    "active": 0,
                    "business_name": "ranking_weekly",
                    "name": "Mingguan",
                    "position_index": 10011,
                    "ranking_id": "weekly",
                    "tab_type": 2,
                    "target_url": "",
                    "ranking_endpoint": "/api/ranking",
                    "ranking_period": "weekly",
                    "source": "custom_ranking"
                },
                {
                    "active": 0,
                    "business_name": "ranking_monthly",
                    "name": "Bulanan",
                    "position_index": 10012,
                    "ranking_id": "monthly",
                    "tab_type": 2,
                    "target_url": "",
                    "ranking_endpoint": "/api/ranking",
                    "ranking_period": "monthly",
                    "source": "custom_ranking"
                },
                {
                    "active": 0,
                    "business_name": "ranking_annually",
                    "name": "Tahunan",
                    "position_index": 10013,
                    "ranking_id": "annually",
                    "tab_type": 2,
                    "target_url": "",
                    "ranking_endpoint": "/api/ranking",
                    "ranking_period": "annually",
                    "source": "custom_ranking"
                }
            ]
            
            target_dict["list"].extend(ranking_tabs)
            data["_note"] = "Tabs updated: module_key replaces tab_key, clean Indonesian names, ranking tabs added"
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Global client instance to reuse session
_global_client = None

def get_client():
    global _global_client
    if _global_client is None:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.client import FreeReelsClient
        _global_client = FreeReelsClient()
        _global_client.login_anonymous()
    return _global_client

# ============================================================
# Direct Client Endpoint (bypass broken proxy)
# ============================================================
@app.post("/api/feed")
async def feed_direct(req: dict):
    """Direct FreeReelsClient feed endpoint with session reuse"""
    client = get_client()
    
    module_key = req.get("module_key", "1040")
    offset = req.get("offset", 0)
    
    # Parse offset dari 'next' parameter jika offset belum di-set
    if offset == 0:
        next_param = req.get("next", "")
        if "offset=" in next_param:
            import re
            match = re.search(r'offset=(\d+)', next_param)
            if match:
                offset = int(match.group(1))
    
    import sys
    print(f"[FEED] module_key={module_key} offset={offset}", file=sys.stderr, flush=True)
    
    # Call direct client
    result = client._request("POST", "/frv2-api/homepage/v2/tab/feed", json={
        "next": f"last_quality=0&offset={offset}&position_index=10000&timestamp=",
        "user_new_theater": False,
        "module_key": str(module_key)
    })
    
    if not result:
        raise HTTPException(status_code=500, detail="Upstream API failed")
    
    items_count = len(result.get("items", []))
    has_more = result.get("page_info", {}).get("has_more", False)
    print(f"[FEED] Response: {items_count} items | has_more={has_more}", file=sys.stderr, flush=True)
    
    # Filter out ranking card items (item_type: "card")
    if "items" in result:
        original_count = len(result["items"])
        result["items"] = [item for item in result["items"] if item.get("item_type") != "card"]
        filtered_count = original_count - len(result["items"])
        if filtered_count > 0:
            print(f"[FEED] Filtered {filtered_count} card items", file=sys.stderr, flush=True)
    
    # Return full upstream response
    return {
        "code": 200,
        "message": "success",
        "data": result
    }

# ============================================================
# Ranking Endpoint
# ============================================================
@app.post("/api/ranking")
@app.get("/api/ranking")
async def get_ranking_endpoint(req: dict = None, period: str = "daily"):
    """
    Get Top 20 ranking dramas by period: daily, weekly, monthly, annually
    Accepts period from query parameter or JSON body {"period": "daily"}
    """
    client = get_client()
    
    selected_period = period
    if req and isinstance(req, dict) and "period" in req:
        selected_period = req.get("period", period)
        
    items = client.get_ranking(period=selected_period)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "period": selected_period,
            "count": len(items),
            "items": items
        }
    }

@app.post("/homepage/v2/rank")
async def homepage_rank(req: dict):
    """
    Ranking endpoint for DramiX frontend
    Accepts JSON body: {"key": "daily"} | {"key": "weekly"} | {"key": "monthly"} | {"key": "annually"}
    """
    client = get_client()
    
    period_key = req.get("key", "daily") if req else "daily"
    
    import sys
    print(f"[RANK] key={period_key}", file=sys.stderr, flush=True)
    
    items = client.get_ranking(period=period_key)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "key": period_key,
            "period": period_key,
            "count": len(items),
            "items": items
        }
    }

@app.get("/homepage/v2/tab/index")
@app.post("/homepage/v2/tab/index")
async def homepage_v2_tab_index(
    req: Optional[dict] = None,
    tab_key: Optional[str] = None,
    position_index: Optional[int] = None
):
    """
    Direct proxy to upstream /homepage/v2/tab/index
    Supports both GET and POST with query params or json body
    """
    client = get_client()
    
    # Extract params from body or query
    tk = tab_key
    pi = position_index
    if req and isinstance(req, dict):
        if not tk and "tab_key" in req:
            tk = req.get("tab_key")
        if pi is None and "position_index" in req:
            pi = req.get("position_index")
    
    tk = str(tk or "622")
    pi = int(pi or 0)
    
    import sys
    print(f"[HOMEPAGE TAB INDEX] tab_key={tk} position_index={pi}", file=sys.stderr, flush=True)
    
    result = client._request("GET", "/frv2-api/homepage/v2/tab/index", params={
        "tab_key": tk,
        "position_index": pi
    })
    
    if not result:
        raise HTTPException(status_code=500, detail="Upstream API failed")
    
    # Flatten nested items structure for tab 622
    raw_items = result.get("items", []) if isinstance(result, dict) else []
    flattened_items = []
    
    if raw_items and isinstance(raw_items, list):
        for section in raw_items:
            if isinstance(section, dict) and "items" in section:
                section_items = section.get("items", [])
                if isinstance(section_items, list):
                    flattened_items.extend(section_items)
    
    if flattened_items:
        result["items"] = flattened_items
    
    items = result.get("items", [])
    if items:
        original_count = len(items)
        result["items"] = [item for item in items if item.get("item_type") != "card"]
        filtered_count = original_count - len(result["items"])
        if filtered_count > 0:
            print(f"[HOMEPAGE TAB INDEX] Filtered {filtered_count} card items", file=sys.stderr, flush=True)
    
    page_info = result.get("page_info", {})
    has_more = page_info.get("has_more", False)
    
    return {
        "code": 200,
        "message": "success",
        "data": result,
        "has_more": has_more
    }

@app.get("/tab/index")
async def tab_index_get(
    tab_key: str = "622",
    position_index: int = 0,
    page: int = 1
):
    """
    GET /tab/index - Endpoint untuk tab khusus seperti Segera Hadir (tab_key=622)
    Menggunakan /homepage/v2/tab/index upstream endpoint
    """
    client = get_client()
    
    import sys
    print(f"[TAB_INDEX] tab_key={tab_key} position_index={position_index} page={page}", file=sys.stderr, flush=True)
    
    result = client._request("GET", "/frv2-api/homepage/v2/tab/index", params={
        "tab_key": str(tab_key),
        "position_index": position_index
    })
    
    if not result:
        raise HTTPException(status_code=500, detail="Upstream API failed")
    
    # Extract and flatten nested items structure
    # Tab 622 returns: {"items": [{"type": "coming_soon_list", "items": [...]}]}
    raw_items = result.get("items", []) if isinstance(result, dict) else []
    flattened_items = []
    
    if raw_items and isinstance(raw_items, list):
        for section in raw_items:
            if isinstance(section, dict) and "items" in section:
                section_items = section.get("items", [])
                if isinstance(section_items, list):
                    flattened_items.extend(section_items)
    
    # Replace with flattened items
    if flattened_items:
        result["items"] = flattened_items
    
    items = result.get("items", [])
    if items:
        original_count = len(items)
        result["items"] = [item for item in items if item.get("item_type") != "card"]
        filtered_count = original_count - len(result["items"])
        if filtered_count > 0:
            print(f"[TAB_INDEX] Filtered {filtered_count} card items", file=sys.stderr, flush=True)
    
    # Flatten pagination
    page_info = result.get("page_info", {})
    has_more = page_info.get("has_more", False)
    
    return {
        "code": 200,
        "message": "success",
        "data": result,
        "has_more": has_more,
        "page": page,
        "next_page": page + 1 if has_more else None
    }

@app.get("/videos")
async def videos_get(
    module_key: Optional[str] = None,
    tab_key: Optional[str] = None,
    page: int = 1,
    position_index: int = 10000
):
    """
    GET /videos - Frontend compatibility endpoint
    Supports: module_key, tab_key, or page-based navigation
    """
    client = get_client()
    
    # Determine module_key from tab_key if needed
    if tab_key and not module_key:
        tab_map = {
            "popular": "1036",
            "new": "1040",
            "woman": "1039",
            "man": "1041",
            "dubbing": "1065",
            "anime": "2204",
        }
        module_key = tab_map.get(tab_key, "1040")
    
    if not module_key:
        module_key = "1040"
    
    offset = (page - 1) * 10
    
    import sys
    print(f"[VIDEOS GET] module_key={module_key} page={page} offset={offset}", file=sys.stderr, flush=True)
    
    result = client._request("POST", "/frv2-api/homepage/v2/tab/feed", json={
        "next": f"last_quality=0&offset={offset}&position_index={position_index}&timestamp=",
        "user_new_theater": False,
        "module_key": str(module_key)
    })
    
    if not result:
        raise HTTPException(status_code=500, detail="Upstream API failed")
    
    if "items" in result:
        original_count = len(result["items"])
        result["items"] = [item for item in result["items"] if item.get("item_type") != "card"]
        filtered_count = original_count - len(result["items"])
        if filtered_count > 0:
            print(f"[VIDEOS GET] Filtered {filtered_count} card items", file=sys.stderr, flush=True)
    
    # Flatten pagination for frontend compatibility
    page_info = result.get("page_info", {})
    has_more = page_info.get("has_more", False)
    next_offset = page_info.get("next", "")
    
    return {
        "code": 200,
        "message": "success",
        "data": result,
        "has_more": has_more,
        "page": page,
        "next_page": page + 1 if has_more else None
    }

# ============================================================
# Proxy Upstream Endpoint (for playground direct testing)
# ============================================================
@app.post("/homepage/v2/tab/feed")
async def homepage_feed_proxy(req: dict):
    """
    Direct proxy to upstream /homepage/v2/tab/feed (same logic as /api/feed)
    """
    import sys
    print(f"[HOMEPAGE FEED] Request received: {req}", file=sys.stderr, flush=True)
    
    try:
        client = get_client()
        
        module_key = req.get("module_key", "1040")
        offset = 0
        
        # Parse offset dari 'next' parameter
        next_param = req.get("next", "")
        if "offset=" in next_param:
            import re
            match = re.search(r'offset=(\d+)', next_param)
            if match:
                offset = int(match.group(1))
        
        print(f"[HOMEPAGE FEED] module_key={module_key} offset={offset}", file=sys.stderr, flush=True)
        
        # Call direct client
        result = client._request("POST", "/frv2-api/homepage/v2/tab/feed", json={
            "next": f"last_quality=0&offset={offset}&position_index=10000&timestamp=",
            "user_new_theater": False,
            "module_key": str(module_key)
        })
        
        if not result:
            raise HTTPException(status_code=500, detail="Upstream API failed")
        
        # Filter out ranking card items
        if "items" in result:
            original_count = len(result["items"])
            result["items"] = [item for item in result["items"] if item.get("item_type") != "card"]
            filtered_count = original_count - len(result["items"])
            if filtered_count > 0:
                print(f"[HOMEPAGE FEED] Filtered {filtered_count} card items", file=sys.stderr, flush=True)
        
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        import traceback
        print(f"[HOMEPAGE FEED] Error: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Drama Info Endpoint
# ============================================================
@app.get("/drama/info_v2")
async def drama_info_v2(series_id: str, scene: int = 1, episode_id: str = None):
    """
    Get drama detail info by series_id
    If episode_id provided, selects that episode from episode_list
    """
    client = get_client()
    
    try:
        # Call upstream endpoint
        result = client._request("GET", "/frv2-api/drama/info_v2", params={
            "series_id": series_id,
            "scene": scene
        })
        
        if not result:
            return {
                "code": 404,
                "message": "Drama not found",
                "data": None
            }
        
        # If episode_id provided, find it in episode_list and set as current episode
        if episode_id and "info" in result and "episode_list" in result["info"]:
            episode_list = result["info"]["episode_list"]
            found = next((ep for ep in episode_list if ep.get("id") == episode_id), None)
            if found:
                result["info"]["episode"] = found
                print(f"[INFO] Selected episode by ID: {episode_id} -> {found.get('name')}")
            else:
                print(f"[WARN] Episode ID {episode_id} not found in episode_list")
        
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }

@app.get("/detail")
async def detail_alias(id: str, episode_id: str = None, episode: int = None):
    """
    Alias for /drama/info_v2 endpoint (frontend compatibility)
    Maps: /detail?id=xxx&episode_id=yyy -> /drama/info_v2?series_id=xxx
    Supports episode_id (UUID) or episode (number)
    """
    result = await drama_info_v2(series_id=id, scene=1, episode_id=episode_id)
    
    # If episode number provided instead of ID, find by index
    if episode and not episode_id and result.get("code") == 200:
        data = result.get("data", {})
        if "info" in data and "episode_list" in data["info"]:
            episode_list = data["info"]["episode_list"]
            idx = episode - 1
            if 0 <= idx < len(episode_list):
                data["info"]["episode"] = episode_list[idx]
                print(f"[INFO] Selected episode by number: {episode} -> {episode_list[idx].get('name')}")
    
    return result

@app.get("/api/episodes")
async def get_episode_stream(id: str, provider: str):
    """
    Get episode playback stream URL and subtitles
    For FreeReels: id is episode_id
    """
    client = get_client()
    
    try:
        # Call upstream get_episode_stream
        result = client.get_episode_stream(id)
        
        if result:
            return {
                "code": 200,
                "message": "success",
                "data": result
            }
        else:
            return {
                "code": 404,
                "message": "Episode not found",
                "data": None
            }
    except Exception as e:
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }

# ============================================================
# Search Endpoint
# ============================================================
def _do_search(keyword: str, search_type: str, page: int):
    """Internal search logic"""
    client = get_client()
    import sys
    print(f"[SEARCH] keyword='{keyword}' type={search_type} page={page}", file=sys.stderr, flush=True)
    
    try:
        result = client._request("POST", "/frv2-api/search/drama", json={
            "keyword": keyword,
            "type": search_type,
            "page": page
        })
        
        if not result:
            # Refresh anonymous credentials and retry
            client.login_anonymous()
            result = client._request("POST", "/frv2-api/search/drama", json={
                "keyword": keyword,
                "type": search_type,
                "page": page
            })
        
        if result:
            return {
                "code": 200,
                "message": "success",
                "data": result
            }
        else:
            return {
                "code": 404,
                "message": "No results found",
                "data": None
            }
    except Exception as e:
        import sys
        print(f"[SEARCH] Error: {str(e)}", file=sys.stderr, flush=True)
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }

@app.get("/search/drama")
async def search_drama_get(keyword: str = "", type: str = "drama", page: int = 1):
    """
    Search dramas by keyword (GET)
    """
    return _do_search(keyword, type, page)

@app.post("/search/drama")
async def search_drama_post(req: dict):
    """
    Search dramas by keyword (POST)
    """
    keyword = req.get("keyword", "")
    search_type = req.get("type", "drama")
    page = req.get("page", 1)
    return _do_search(keyword, search_type, page)

# ============================================================
# Dashboard HTML
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>FreeReels API</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --border: rgba(148,163,184,0.2);
            --accent: #10b981;
            --text: #f1f5f9;
            --dim: #94a3b8;
            --code: rgba(15,23,42,0.6);
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        html { font-size: 16px; }
        
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .header {
            background: var(--card);
            border-bottom: 1px solid var(--border);
            padding: 16px 20px;
        }
        
        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--dim);
        }
        
        .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
            flex-shrink: 0;
        }
        
        .grid {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 16px 20px;
        }
        
        @media (min-width: 768px) {
            .grid {
                display: grid;
                grid-template-columns: 280px 1fr;
                padding: 20px;
            }
        }
        
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }
        
        .card-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }
        
        .sidebar { display: flex; flex-direction: column; gap: 12px; }
        .main { display: flex; flex-direction: column; gap: 12px; }
        
        .btn-list { display: flex; flex-direction: column; gap: 6px; }
        
        .btn {
            background: rgba(16,185,129,0.1);
            border: 1px solid rgba(16,185,129,0.3);
            color: var(--accent);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            text-align: left;
            font-family: 'Courier New', monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: background 0.2s;
        }
        
        .btn:hover { background: rgba(16,185,129,0.2); }
        
        .btn:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        label {
            font-size: 0.8rem;
            color: var(--dim);
            font-weight: 500;
        }
        
        input, select, textarea {
            background: var(--code);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            width: 100%;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: 2px solid var(--accent);
            outline-offset: -1px;
            border-color: var(--accent);
        }
        
        textarea {
            resize: vertical;
            min-height: 60px;
        }
        
        .btn-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .btn-primary, .btn-secondary {
            padding: 10px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            flex: 1;
            min-width: 120px;
        }
        
        @media (max-width: 480px) {
            .btn-primary, .btn-secondary { min-width: 100%; }
        }
        
        .btn-primary {
            background: var(--accent);
            color: var(--bg);
            border: none;
        }
        
        .btn-primary:hover { opacity: 0.9; }
        
        .btn-primary:focus-visible {
            outline: 2px solid var(--text);
            outline-offset: 2px;
        }
        
        .btn-secondary {
            background: rgba(16,185,129,0.1);
            color: var(--accent);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }
        
        .response-box {
            background: var(--code);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            max-height: 300px;
            overflow-y: auto;
            overflow-x: hidden;
        }
        
        .response-header {
            font-size: 0.8rem;
            color: var(--dim);
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .response-code {
            font-family: 'Courier New', monospace;
            color: var(--accent);
            font-size: 0.8rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-word;
            overflow-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 FreeReels API</h1>
        <div class="status">
            <div class="dot"></div>
            <span id="status">Loading...</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="sidebar">
            <div class="card">
                <div class="card-title">Categories</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=503&position_index=0')">Popular (503)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=504&position_index=0')">Perempuan (504)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=505&position_index=0')">New (505)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=506&position_index=0')">Laki-Laki (506)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=516&position_index=0')">Dubbing (516)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=547&position_index=0')">Anime (547)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/index','tab_key=622&position_index=0')">Segera Hadir (622)</button>
                    <button class="btn" onclick="set('GET','/homepage/v2/tab/list','')">All Tabs List</button>
                    <button class="btn" onclick="set('GET','/api/tabs/complete','')">Tabs + Anime</button>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Ranking (Top 20 Leaderboard)</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('POST','/homepage/v2/rank','{&quot;key&quot;:&quot;daily&quot;}')">Harian (Daily)</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/rank','{&quot;key&quot;:&quot;weekly&quot;}')">Mingguan (Weekly)</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/rank','{&quot;key&quot;:&quot;monthly&quot;}')">Bulanan (Monthly)</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/rank','{&quot;key&quot;:&quot;annually&quot;}')">Tahunan (Annually)</button>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Segera Hadir (Coming Soon)</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('GET','/tab/index','tab_key=622&position_index=0&page=1')">Segera Hadir (622) page=1</button>
                    <button class="btn" onclick="set('GET','/tab/index','tab_key=622&position_index=10&page=2')">Segera Hadir (622) page=2</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/index','{&quot;tab_key&quot;:&quot;622&quot;,&quot;position_index&quot;:0}')">Tab Index 622 (POST)</button>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Feed / Pagination (Real App)</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1036&quot;}')">Popular (1036) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1039&quot;}')">Perempuan (1039) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1040&quot;}')">New (1040) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1041&quot;}')">Laki-Laki (1041) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1065&quot;}')">Dubbing (1065) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=0&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;2204&quot;}')">Anime (2204) offset=0</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=10&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1040&quot;}')">New (1040) offset=10</button>
                    <button class="btn" onclick="set('POST','/homepage/v2/tab/feed','{&quot;next&quot;:&quot;last_quality=0&amp;offset=50&amp;position_index=10000&amp;timestamp=&quot;,&quot;user_new_theater&quot;:false,&quot;module_key&quot;:&quot;1065&quot;}')">Dubbing (1065) offset=50</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Search</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('GET','/search/hot_words','')">Hot Words</button>
                    <button class="btn" onclick="set('GET','/search/trending_searches','')">Trending</button>
                    <button class="btn" onclick="set('GET','/search/audio-tabs','')">Audio Tabs</button>
                    <button class="btn" onclick="set('POST','/search/drama','{&quot;keyword&quot;:&quot;love&quot;,&quot;type&quot;:&quot;drama&quot;}')">Search Drama</button>
                    <button class="btn" onclick="set('POST','/search/suggestion','{&quot;keyword&quot;:&quot;rom&quot;}')">Suggestions</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Content</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('GET','/drama/info_v2','series_id=eAiS7aYiYQ&scene=1')">Drama Detail</button>
                    <button class="btn" onclick="set('GET','/drama/v3/follow_list','')">Following</button>
                    <button class="btn" onclick="set('GET','/drama/v3/view_history','')">History</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">Account</div>
                <div class="btn-list">
                    <button class="btn" onclick="set('GET','/user/profilev2','')">Profile</button>
                    <button class="btn" onclick="set('GET','/wallet/my','')">Wallet</button>
                    <button class="btn" onclick="auth()">Refresh Auth</button>
                </div>
            </div>
        </div>
        
        <div class="main">
            <div class="card">
                <div class="card-title">API Tester</div>
                
                <div class="form-group">
                    <label>Method</label>
                    <select id="method">
                        <option>GET</option>
                        <option>POST</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Endpoint</label>
                    <input id="endpoint" type="text" placeholder="/drama/info_v2" value="/drama/info_v2">
                </div>
                
                <div class="form-group">
                    <label>Query / Body</label>
                    <textarea id="params" placeholder="series_id=eAiS7aYiYQ&scene=1"></textarea>
                </div>
                
                <div class="btn-group">
                    <button class="btn-primary" onclick="run()">Run Test</button>
                    <button class="btn-secondary" onclick="copy()">Copy JSON</button>
                </div>
            </div>
            
            <div class="card">
                <div class="response-header">
                    <span>Response</span>
                    <span id="meta">Status: -</span>
                </div>
                <div class="response-box">
                    <div class="response-code" id="resp">// Click Run Test</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', auth);
        
        async function auth() {
            try {
                await fetch('/api/auth/login', { method: 'POST' });
                const r = await fetch('/api/auth/status');
                const d = await r.json();
                document.getElementById('status').textContent = d.authenticated 
                    ? `Connected as ${d.user_name} (${d.token_preview})`
                    : 'Not authenticated';
            } catch (e) {
                document.getElementById('status').textContent = 'Error: ' + e.message;
            }
        }
        
        function set(method, endpoint, params) {
            document.getElementById('method').value = method;
            document.getElementById('endpoint').value = endpoint;
            document.getElementById('params').value = params;
        }
        
        async function run() {
            const method = document.getElementById('method').value;
            const endpoint = document.getElementById('endpoint').value;
            const paramsStr = document.getElementById('params').value;
            
            const el = document.getElementById('resp');
            const meta = document.getElementById('meta');
            
            el.textContent = 'Loading...';
            
            try {
                // Direct fetch for custom endpoints
                if (endpoint.startsWith('/api/')) {
                    const start = performance.now();
                    let r;
                    
                    if (method === 'POST' && paramsStr) {
                        // POST request with body
                        let body;
                        try { 
                            body = JSON.parse(paramsStr);
                        } catch { 
                            body = { raw: paramsStr };
                        }
                        
                        r = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                    } else {
                        // GET request
                        r = await fetch(endpoint);
                    }
                    
                    const elapsed = performance.now() - start;
                    const data = await r.json();
                    
                    el.textContent = JSON.stringify(data, null, 2);
                    meta.textContent = `Status: ${r.status} | Time: ${elapsed.toFixed(0)}ms`;
                    return;
                }
                
                // Handle /tab/index endpoint
                if (endpoint === '/tab/index') {
                    const start = performance.now();
                    const url = paramsStr ? `${endpoint}?${paramsStr}` : endpoint;
                    const r = await fetch(url);
                    const elapsed = performance.now() - start;
                    const result = await r.json();
                    el.textContent = JSON.stringify(result, null, 2);
                    meta.textContent = `Status: ${result.code} | Items: ${result.data?.items?.length || 0} | Time: ${elapsed.toFixed(0)}ms`;
                    return;
                }

                // Handle /homepage/v2/tab/index
                if (endpoint === '/homepage/v2/tab/index') {
                    const start = performance.now();
                    let body = {};
                    if (method === 'POST' && paramsStr) {
                        try { body = JSON.parse(paramsStr); } catch { body = { raw: paramsStr }; }
                        const r = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(body)
                        });
                        const elapsed = performance.now() - start;
                        const result = await r.json();
                        el.textContent = JSON.stringify(result, null, 2);
                        meta.textContent = `Status: ${result.code} | Items: ${result.data?.items?.length || 0} | Time: ${elapsed.toFixed(0)}ms`;
                        return;
                    } else {
                        const url = paramsStr ? `${endpoint}?${paramsStr}` : endpoint;
                        const r = await fetch(url);
                        const elapsed = performance.now() - start;
                        const result = await r.json();
                        el.textContent = JSON.stringify(result, null, 2);
                        meta.textContent = `Status: ${result.code} | Items: ${result.data?.items?.length || 0} | Time: ${elapsed.toFixed(0)}ms`;
                        return;
                    }
                }
                
                // Handle /search/drama
                if (endpoint === '/search/drama') {
                    const start = performance.now();
                    let body = {};
                    if (paramsStr) {
                        try { body = JSON.parse(paramsStr); } catch { body = { raw: paramsStr }; }
                    }
                    const r = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const elapsed = performance.now() - start;
                    const result = await r.json();
                    el.textContent = JSON.stringify(result, null, 2);
                    const itemCount = result.data?.items?.length || 0;
                    meta.textContent = `Status: ${result.code} | Results: ${itemCount} | Time: ${elapsed.toFixed(0)}ms`;
                    return;
                }
                
                // Handle /drama/info_v2
                if (endpoint === '/drama/info_v2') {
                    const start = performance.now();
                    const url = paramsStr ? `${endpoint}?${paramsStr}` : endpoint;
                    const r = await fetch(url);
                    const elapsed = performance.now() - start;
                    const result = await r.json();
                    el.textContent = JSON.stringify(result, null, 2);
                    meta.textContent = `Status: ${result.code} | Time: ${elapsed.toFixed(0)}ms`;
                    return;
                }
            } catch (e) {
                el.textContent = 'Error: ' + e.message;
                el.style.color = '#ef4444';
            }
        }
        
        function copy() {
            const text = document.getElementById('resp').textContent;
            if (!text) return;

            function showSuccess() {
                const btn = document.querySelector('button[onclick="copy()"]');
                if (btn) {
                    const orig = btn.textContent;
                    btn.textContent = 'Copied! ✓';
                    setTimeout(() => { btn.textContent = orig; }, 2000);
                }
            }

            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(showSuccess).catch(() => fallbackCopy(text));
            } else {
                fallbackCopy(text);
            }

            function fallbackCopy(val) {
                const ta = document.createElement('textarea');
                ta.value = val;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                ta.style.top = '0';
                document.body.appendChild(ta);
                ta.focus();
                ta.select();
                try {
                    document.execCommand('copy');
                    showSuccess();
                } catch (e) {
                    alert('Gagal copy: ' + e.message);
                }
                document.body.removeChild(ta);
            }
        }
    </script>
</body>
</html>
""", media_type="text/html")

# ============================================================
# Health Check
# ============================================================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "authenticated": bool(state.oauth_token),
        "timestamp": datetime.now().isoformat(),
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 7406))
    uvicorn.run(app, host=host, port=port)
