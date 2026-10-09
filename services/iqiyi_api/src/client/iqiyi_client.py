"""iQIYI API client for authentication and catalog requests."""
import asyncio
import json
import re
import time
from typing import Dict, Any, Optional, List
import urllib.parse
import httpx
from src.client.session_store import SessionStore
from src.client.signer import Signer
from src.models.schemas import (
    StreamQuality,
    SubtitleItem,
    AudioTrackItem,
    PlaybackData,
)
from src.utils.crypto import PasswordEncryptor

BID_MAP = {
    100: "240p",
    200: "360p",
    300: "480p",
    400: "540p",
    500: "720p",
    600: "1080p",
    610: "1080p50",
    700: "2k",
    800: "4k",
}

LID_MAP = {
    1: ("Chinese (Simplified)", "zh-CN"),
    2: ("Chinese (Traditional)", "zh-TW"),
    3: ("English", "en"),
    4: ("Korean", "ko"),
    5: ("Japanese", "ja"),
    6: ("French", "fr"),
    18: ("Thai", "th"),
    21: ("Malay", "ms"),
    23: ("Vietnamese", "vi"),
    24: ("Bahasa Indonesia", "id"),
    26: ("Spanish", "es"),
    27: ("Portuguese", "pt"),
    28: ("Arabic", "ar"),
}


class LoginError(Exception):
    """Raised when login to iQIYI fails."""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Login failed: {code} - {message}")


class PlaybackError(Exception):
    """Raised when playback resolving fails."""
    
    def __init__(self, message: str, code: int = 404):
        self.message = message
        self.code = code
        super().__init__(f"Playback error ({code}): {message}")


class IQIYIClient:
    """Client for iQIYI API authentication and catalog operations."""

    LOGIN_URL = "https://passport.iq.com/intl/reglogin/mobile_login.action"
    TIMEOUT = 30

    def __init__(self, session_store: Optional[SessionStore] = None):
        """
        Initialize iQIYI client.
        
        Args:
            session_store: SessionStore instance (default: local data/sessions.json)
        """
        self.session_store = session_store or SessionStore()
        self._http_client = None
        self._m3u8_cache: Dict[Tuple[str, int], str] = {}

    def _get_http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=self.TIMEOUT)
        return self._http_client

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with iQIYI and save session.
        
        Args:
            username: Phone number or email
            password: Plaintext password
            
        Returns:
            Session dict with auth_cookie, device_id, vip_status, etc.
            
        Raises:
            LoginError: If authentication fails
        """
        # Encrypt password
        encrypted_pwd = PasswordEncryptor.encrypt_password(password)
        
        # Build request body
        body = Signer.build_auth_body(
            username=username,
            encrypted_password=encrypted_pwd,
        )
        
        # Build headers with signature
        sign_value = Signer.calculate_request_sign(body)
        pass_sign = Signer.generate_pass_sign()
        
        headers = Signer.build_headers(extra_headers={
            "Sign": sign_value,
            "Pass-Sign": pass_sign,
        })
        
        # POST to login endpoint
        try:
            client = self._get_http_client()
            response = client.post(
                self.LOGIN_URL,
                content=body,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            raise LoginError("NETWORK_ERROR", str(e))
        except httpx.HTTPStatusError as e:
            raise LoginError("HTTP_ERROR", f"HTTP {e.response.status_code}")
        
        # Parse response
        try:
            response_data = response.json()
        except Exception as e:
            raise LoginError("PARSE_ERROR", f"Invalid response format: {e}")
        
        # Check response code
        code = response_data.get("code", "")
        message = response_data.get("msg", "Unknown error")
        
        if code != "P00000":
            raise LoginError(code, message)
        
        # Extract session information
        session = self._extract_session(
            username=username,
            response=response,
            response_data=response_data
        )
        
        # Save session
        self.session_store.save(session)
        return session

    @staticmethod
    def _extract_session(username: str, response: httpx.Response, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract session information from login response.
        
        Args:
            username: Account identifier
            response: HTTP response object
            response_data: Parsed JSON response
            
        Returns:
            Session dict
        """
        # Extract cookies from Set-Cookie headers
        cookies = response.headers.get("set-cookie", "")
        auth_cookie = "; ".join([c.split(";")[0] for c in cookies.split(",")])
        
        # Parse cookie data
        cookie_data = {}
        for cookie in auth_cookie.split(";"):
            if "=" in cookie:
                key, val = cookie.strip().split("=", 1)
                cookie_data[key] = val
        
        # Extract VIP status from response
        vip_status = response_data.get("data", {}).get("vipStatus", False) if isinstance(response_data.get("data"), dict) else False
        vip_type = response_data.get("data", {}).get("vipType", None) if isinstance(response_data.get("data"), dict) else None
        
        session = {
            "account_identifier": username,
            "auth_cookie": auth_cookie,
            "cookie_data": cookie_data,
            "device_id": Signer.DEFAULT_DEVICE_ID,
            "vip_status": bool(vip_status),
            "vip_type": vip_type,
            "vip_expires_at": None,
            "is_active": True,
        }
        
        return session

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        Get active session from store.
        
        Returns:
            Session dict or None if no active session
        """
        return self.session_store.read()

    def get_auth_cookie(self) -> Optional[str]:
        """
        Get auth cookie string from active session.
        
        Returns:
            Cookie string or None
        """
        session = self.get_active_session()
        return session.get("auth_cookie") if session else None

    def check_vip_status(self) -> Dict[str, Any]:
        """
        Actively query iQIYI pcw-api (pvvp) to verify real-time VIP subscription status.
        
        Automatically synchronizes local session_store so VIP status is never hardcoded.
        
        Returns:
            Dict containing live is_active, vip_status, vip_type, and vip_expires_at.
        """
        session = self.get_active_session()
        if not session or not session.get("is_active", False):
            return {
                "is_active": False,
                "vip_status": False,
                "vip_type": None,
                "vip_expires_at": None,
                "account_identifier": None,
            }

        cookie_str = self.get_auth_cookie()
        if not cookie_str:
            return {
                "is_active": False,
                "vip_status": False,
                "vip_type": None,
                "vip_expires_at": None,
                "account_identifier": session.get("account_identifier"),
            }

        client = self._get_http_client()
        url = "https://pcw-api.iq.com/api/pvvp"
        params = {
            "version": "1.0",
            "vipInfoVersion": "5.0",
            "langCode": "en_us",
            "modeCode": "intl",
            "platformId": "3",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie_str,
            "Referer": "https://www.iq.com/",
        }

        try:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                res_data = resp.json()
                if res_data.get("code") == "0":
                    data = res_data.get("data", {}) or {}
                    vip_list = data.get("vip_list") or []

                    is_vip = False
                    vip_type = None
                    vip_expires_at = None

                    for v in vip_list:
                        # status "1" represents active subscription
                        if str(v.get("status")) == "1":
                            is_vip = True
                            vip_type = v.get("name") or v.get("type") or "VIP"
                            deadline = v.get("deadline")
                            if deadline:
                                vip_expires_at = str(deadline)
                            break

                    # Auto-update session store if status changed
                    if session.get("vip_status") != is_vip or session.get("vip_type") != vip_type:
                        session["vip_status"] = is_vip
                        session["vip_type"] = vip_type
                        session["vip_expires_at"] = vip_expires_at
                        self.session_store.save(session)

                    return {
                        "is_active": True,
                        "vip_status": is_vip,
                        "vip_type": vip_type,
                        "vip_expires_at": vip_expires_at,
                        "account_identifier": session.get("account_identifier"),
                    }
        except Exception:
            pass

        # Fallback to local session store
        return {
            "is_active": session.get("is_active", True),
            "vip_status": session.get("vip_status", False),
            "vip_type": session.get("vip_type"),
            "vip_expires_at": session.get("vip_expires_at"),
            "account_identifier": session.get("account_identifier"),
        }

    def _get_common_params(self) -> Dict[str, str]:
        """
        Build authentic device and session query parameters for iQIYI requests.
        """
        session = self.get_active_session() or {}
        device_id = session.get("device_id") or Signer.DEFAULT_DEVICE_ID
        cookie_data = session.get("cookie_data") or {}
        
        auth_cookie = (
            cookie_data.get("I00001")
            or (session.get("auth_cookie", "").split("I00001=")[-1].split(";")[0] if "I00001=" in session.get("auth_cookie", "") else "")
            or ""
        )
        
        uid = session.get("uid", "")
        if not uid and "I00002" in cookie_data:
            try:
                raw = urllib.parse.unquote(cookie_data["I00002"])
                parsed = json.loads(raw)
                uid = str(parsed.get("data", {}).get("uid", ""))
            except Exception:
                pass
        if not uid:
            uid = "30111882297"
            
        now_ms = str(int(time.time() * 1000))
        return {
            "app_k": "20911006a509e62d0901460c7b8b61a4",
            "app_v": "8.1.5",
            "app_t": "i18nvideo",
            "platform_id": "1070",
            "dev_os": "13",
            "dev_ua": "Redmi 5 Plus",
            "net_sts": "1",
            "qyid": device_id,
            "scrn_scale": "1",
            "p_dolby": "1",
            "p_4k": "1",
            "psp_uid": uid,
            "psp_cki": auth_cookie,
            "psp_status": "1" if auth_cookie else "-1",
            "secure_v": "1",
            "secure_p": "GPhone",
            "core": "4",
            "customized": "1",
            "lang": "id_id",
            "app_lm": "id",
            "mod": "id",
            "timezone": "GMT+7",
            "aqyid": device_id,
            "req_times": "0",
            "req_sn": now_ms,
        }

    def search(self, keyword: str, pg_num: int = 1, lang: str = "id_id") -> Dict[str, Any]:
        """
        Search iQIYI catalog with keyword and pagination.
        
        Args:
            keyword: Search query
            pg_num: Page index (default: 1)
            lang: Language code (default: id_id)
            
        Returns:
            Dict containing keyword, pg_num, has_more, and items list
        """
        search_url = "https://api.iq.com/api/search?layout_v=88.9999.1609835749"
        params = self._get_common_params()
        params.update({
            "keyword": keyword,
            "pg_num": str(pg_num),
            "lang": lang,
        })
        
        headers = Signer.build_headers()
        cookie = self.get_auth_cookie()
        if cookie:
            headers["Cookie"] = cookie
            
        client = self._get_http_client()
        response = client.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        datas = data.get("data", {}).get("datas", []) or []
        
        items = []
        for it in datas:
            video_info = it.get("video_info")
            if not video_info:
                continue
                
            album_id = str(video_info.get("album_id") or it.get("id") or "")
            title = video_info.get("title") or ""
            genre = video_info.get("channel_name") or "Drama"
            desc = ""
            tags = []
            year = None

            raw_img = video_info.get("image") or ""
            if raw_img.startswith("//"):
                raw_img = f"https:{raw_img}"
                
            vertical_cover = raw_img
            horizontal_banner = None
            if raw_img:
                if re.search(r"_\d+_\d+\.(webp|jpg|png)$", raw_img):
                    vertical_cover = re.sub(r"_\d+_\d+\.(webp|jpg|png)$", "_260_360.jpg", raw_img)
                    horizontal_banner = re.sub(r"_\d+_\d+\.(webp|jpg|png)$", "_1013_569.jpg", raw_img)
                else:
                    horizontal_banner = raw_img
                    
            for info in video_info.get("detail_infos", []):
                type_id = info.get("type_id")
                content = info.get("content", "")
                if type_id == 22:
                    desc = content
                elif type_id == 101:
                    parts = [p.strip() for p in content.split("|")]
                    for p in parts:
                        if p.isdigit() and len(p) == 4:
                            year = int(p)
                        elif p:
                            tags.append(p)
                    if parts:
                        genre = parts[-1]
                elif type_id == 11:
                    cast_str = content.strip()
                    if cast_str:
                        tags.extend([c.strip() for c in cast_str.split(",")])
            
            total_episodes = None
            is_vip = False
            for mark in video_info.get("marks", []):
                text = mark.get("text", "")
                if "episodes" in text.lower():
                    m = re.search(r"(\d+)", text)
                    if m:
                        total_episodes = int(m.group(1))
                num = str(mark.get("num", ""))
                if num in ["206", "218"]:
                    is_vip = True
                    
            items.append({
                "id": album_id,
                "name": title,
                "desc": desc,
                "cover": vertical_cover or raw_img,
                "banner": horizontal_banner,
                "covers": {
                    "vertical": vertical_cover or raw_img,
                    "horizontal": horizontal_banner,
                },
                "genre": genre,
                "tags": tags,
                "year": year,
                "vip_status": is_vip,
                "total_episodes": total_episodes,
            })
            
        return {
            "keyword": keyword,
            "pg_num": pg_num,
            "has_more": len(items) > 0,
            "items": items,
        }

    def get_feed(self) -> list:
        """
        Fetch curated homepage feed items.
        
        Returns:
            List of feed items
        """
        try:
            search_res = self.search(keyword="trending", pg_num=1)
            items = []
            for item in search_res.get("items", []):
                items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "cover": item.get("cover"),
                    "banner": item.get("banner"),
                    "covers": item.get("covers"),
                    "desc": item.get("desc"),
                    "badge": item.get("genre") or "Hot",
                    "is_vip": item.get("vip_status", False),
                })
            return items
        except Exception:
            return []

    def get_tabs(self) -> list:
        """
        Fetch curated navigation tabs.
        
        Returns:
            List of navigation tabs
        """
        nav_url = "https://api.iq.com/control/library_nav"
        params = self._get_common_params()
        headers = Signer.build_headers()
        cookie = self.get_auth_cookie()
        if cookie:
            headers["Cookie"] = cookie
            
        try:
            client = self._get_http_client()
            resp = client.get(nav_url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data and isinstance(data, list):
                    tabs = []
                    for d in data:
                        tabs.append({
                            "tab_key": str(d.get("channel_id") or d.get("page_key")),
                            "name": d.get("title", ""),
                            "module_key": d.get("page_key"),
                        })
                    if tabs:
                        return tabs
        except Exception:
            pass
            
        return [
            {"tab_key": "2", "name": "Drama", "module_key": "home_drama"},
            {"tab_key": "4", "name": "Anime", "module_key": "home_anime"},
            {"tab_key": "6", "name": "Variety Show", "module_key": "home_variety"},
            {"tab_key": "1", "name": "Movie", "module_key": "home_movie"},
            {"tab_key": "35", "name": "Short", "module_key": "home_short_new"},
        ]

    def _fetch_play_data(self, album_id: str) -> Dict[str, Any]:
        """Fetch play data for an album containing series metadata and episodes."""
        play_url = "https://api.iq.com/api/play_data"
        params = self._get_common_params()
        params.update({
            "type": "vertical_play_page",
            "album_id": str(album_id),
            "fetch_all": "true",
        })
        headers = Signer.build_headers()
        cookie = self.get_auth_cookie()
        if cookie:
            headers["Cookie"] = cookie

        client = self._get_http_client()
        resp = client.get(play_url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_drama_info(self, album_id: str, lang: str = "id_id") -> Dict[str, Any]:
        """
        Fetch rich metadata for a single drama series including synopsis, cast,
        director, score, age rating, and categories.
        
        Args:
            album_id: Album / series identifier
            lang: Language code for localized metadata (default "id_id")
            
        Returns:
            Drama metadata dictionary
        """
        data = self._fetch_play_data(album_id)
        album = data.get("album", {})
        share = data.get("share", {})
        episodes_raw = data.get("episodes", [])
        
        tags = list(album.get("tags", []))
        year = None
        for t in tags:
            if isinstance(t, str) and t.isdigit() and len(t) == 4:
                year = int(t)
                break
                
        cover = share.get("image_url") or ""
        if not cover and episodes_raw:
            cover = episodes_raw[0].get("image_url") or ""
        banner: Optional[str] = None
            
        is_any_vip = any(ep.get("charge_status") == 2 or bool(ep.get("mark")) for ep in episodes_raw)
        total_eps = len(episodes_raw) or data.get("page_info", {}).get("total")
        
        name = album.get("title") or ""
        desc = ""
        score: Optional[str] = None
        score_votes: Optional[int] = None
        rating: Optional[str] = None
        directors: List[str] = []
        main_actors: List[str] = []
        is_original = False
        categories: Optional[Dict[str, List[str]]] = None
        
        # Attempt to retrieve full SSR metadata from web album page
        h5_link = share.get("h5_link", "")
        slug = urllib.parse.urlparse(h5_link).path.strip("/").split("/")[-1] if h5_link else ""
        if not slug and str(album_id):
            slug = str(album_id)
            
        directors: List[Dict[str, Any]] = []
        main_actors: List[Dict[str, Any]] = []

        if slug:
            try:
                client = self._get_http_client()
                album_url = f"https://www.iq.com/album/{slug}"
                accept_lang = "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7" if "id" in lang.lower() else "en-US,en;q=0.9"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.iq.com/",
                    "Accept-Language": accept_lang,
                    "Cookie": f"lang={lang}",
                }
                params = {"lang": lang}
                resp = client.get(album_url, params=params, headers=headers)
                if resp.status_code == 200 and '<script id="__NEXT_DATA__"' in resp.text:
                    tag = '<script id="__NEXT_DATA__" type="application/json">'
                    nd_str = resp.text.split(tag, 1)[1].split("</script>", 1)[0]
                    nd = json.loads(nd_str)
                    album_state = nd.get("props", {}).get("initialState", {}).get("album", {})
                    vai = album_state.get("videoAlbumInfo", {})
                    score_info = album_state.get("albumScoreInfo", {})
                    
                    if vai.get("name"):
                        name = vai.get("name")
                    if vai.get("desc"):
                        desc = vai.get("desc")
                        
                    # 1. High-res horizontal landscape banner (16:9)
                    raw_banner = (
                        vai.get("albumFocus1024")
                        or vai.get("albumFocusH5")
                        or vai.get("albumFocus125")
                        or vai.get("thumbnailUrl1")
                        or vai.get("schemaAlbumImage")
                    )
                    if raw_banner:
                        banner = f"https:{raw_banner}" if raw_banner.startswith("//") else raw_banner
                        
                    # 2. High-res vertical portrait poster (3:4)
                    raw_vertical = (
                        vai.get("thumbnailUrl2")
                        or vai.get("albumPic260")
                        or share.get("image_url")
                    )
                    if raw_vertical:
                        cover = f"https:{raw_vertical}" if raw_vertical.startswith("//") else raw_vertical
                    elif banner and re.search(r"_\d+_\d+\.(webp|jpg|png)$", banner):
                        cover = re.sub(r"_\d+_\d+\.(webp|jpg|png)$", "_260_360.jpg", banner)
                    else:
                        cover = banner

                    if not banner and cover and re.search(r"_\d+_\d+\.(webp|jpg|png)$", cover):
                        banner = re.sub(r"_\d+_\d+\.(webp|jpg|png)$", "_1013_569.jpg", cover)
                        
                    # Map star photos from starEnterArr
                    star_enter = vai.get("starEnterArr") or []
                    star_map: Dict[str, Dict[str, Any]] = {}
                    for s in star_enter:
                        if isinstance(s, dict) and s.get("name"):
                            star_map[s["name"].strip().lower()] = s
                            
                    dir_raw = vai.get("dirArr") or []
                    for d in dir_raw:
                        if isinstance(d, dict) and d.get("name"):
                            d_name = d["name"].strip()
                            s_info = star_map.get(d_name.lower(), {})
                            img = s_info.get("headPic") or s_info.get("coverPic")
                            sid = str(s_info.get("starId") or s_info.get("id") or "")
                            directors.append({
                                "id": sid or None,
                                "name": d_name,
                                "image": img,
                                "role": "Sutradara",
                            })
                            
                    actor_raw = vai.get("actorArr") or []
                    for a in actor_raw:
                        if isinstance(a, dict) and a.get("name"):
                            a_name = a["name"].strip()
                            s_info = star_map.get(a_name.lower(), {})
                            img = s_info.get("headPic") or s_info.get("coverPic")
                            sid = str(s_info.get("starId") or s_info.get("id") or "")
                            main_actors.append({
                                "id": sid or None,
                                "name": a_name,
                                "image": img,
                                "role": "Pemeran Utama",
                            })
                    
                    if score_info.get("isShowScore") and score_info.get("score"):
                        score = str(score_info.get("score"))
                        score_votes = score_info.get("totalVotes")
                        
                    rating = vai.get("rating")
                    if vai.get("year"):
                        year = int(vai.get("year"))
                    if vai.get("total") or vai.get("maxOrder"):
                        total_eps = vai.get("total") or vai.get("maxOrder")
                        
                    is_original = bool(vai.get("isExclusive") or vai.get("isQiyiProduced"))
                    
                    cat_map = vai.get("categoryTagMap", {})
                    if cat_map:
                        categories = {}
                        for c_k, c_v in cat_map.items():
                            if isinstance(c_v, list):
                                categories[c_k] = [
                                    item.get("name") for item in c_v 
                                    if isinstance(item, dict) and item.get("name")
                                ]
            except Exception:
                pass
                
        # 1. Badges: Header summary badges
        badges: List[str] = []
        if is_original:
            badges.append("Original")
        if score:
            badges.append(str(score))
        if rating:
            badges.append(rating)
        if year:
            badges.append(str(year))
        if total_eps:
            badges.append(f"{total_eps} Episode")
            
        # 2. Tags: Pure category and genre tags matching iQIYI display order
        clean_tags: List[str] = []
        if categories:
            for preferred_group in ["Place", "TypeDsj", "SubjectMatter", "Language", "Adaptation"]:
                for item_name in categories.get(preferred_group, []):
                    if item_name not in clean_tags:
                        clean_tags.append(item_name)
            for group_items in categories.values():
                for item_name in group_items:
                    if item_name not in clean_tags:
                        clean_tags.append(item_name)
                        
        if not clean_tags:
            clean_tags = [t for t in tags if not (t.isdigit() or t in ["13+", "18+", "16+"])]
                
        primary_genre = "Drama"
        if categories and "TypeDsj" in categories and categories["TypeDsj"]:
            primary_genre = categories["TypeDsj"][0]
        elif clean_tags:
            primary_genre = clean_tags[0]
            
        if cover:
            if cover.startswith("//"):
                cover = f"https:{cover}"
            if not banner and re.search(r"_\d+_\d+\.(webp|jpg|png)$", cover):
                banner = re.sub(r"_\d+_\d+\.(webp|jpg|png)$", "_1013_569.jpg", cover)
        if banner and banner.startswith("//"):
            banner = f"https:{banner}"

        return {
            "id": str(album.get("album_id") or album_id),
            "name": name,
            "desc": desc,
            "cover": cover,
            "banner": banner,
            "covers": {
                "vertical": cover,
                "horizontal": banner,
            },
            "genre": primary_genre,
            "badges": badges,
            "tags": clean_tags,
            "year": year,
            "vip_status": is_any_vip,
            "total_episodes": total_eps,
            "score": score,
            "score_votes": score_votes,
            "rating": rating,
            "directors": directors,
            "main_actors": main_actors,
            "is_original": is_original,
            "categories": categories,
        }

    def get_episodes(self, album_id: str) -> list:
        """
        Fetch episode list for a drama.
        
        Args:
            album_id: Series / album identifier
            
        Returns:
            List of episode dictionaries
        """
        data = self._fetch_play_data(album_id)
        raw_list = data.get("episodes", [])
        
        episodes = []
        for idx, ep in enumerate(raw_list):
            order = ep.get("order") or (idx + 1)
            title = (ep.get("title") or f"Episode {order}").strip()
            is_vip = ep.get("charge_status") == 2 or bool(ep.get("mark"))
            episodes.append({
                "episode_number": order,
                "title": title,
                "duration": ep.get("duration"),
                "is_vip": is_vip,
                "subtitles": ["en", "id"],
                "video_id": str(ep.get("tv_id") or ""),
            })
        return episodes

    def _resolve_playback_mobile(self, tv_id: str, album_id: str) -> PlaybackData:
        """
        Resolve short drama playback via mobile /video/play endpoint.
        
        Args:
            tv_id: Episode TV ID
            album_id: Album ID for the short drama
            
        Returns:
            PlaybackData object
            
        Raises:
            PlaybackError: If resolution fails
        """
        tv_id_str = str(tv_id).strip()
        album_id_str = str(album_id).strip()
        
        client = self._get_http_client()
        cookie_str = self.get_auth_cookie()
        
        # Build parameters for /video/play endpoint
        params = self._get_common_params()
        params.update({
            "tv_id": tv_id_str,
            "album_id": album_id_str,
            "play_retry": "0",
            "content_type": "1,2",
            "play_res": "0",
            "play_core": "1",
            "sdk_v": "20000870",
            "abiFilter": "1",
            "sdk_build": "870.0.1190",
            "sdk_ctrl_v": "11.9.0",
            "src": "20",
            "rpage": "half_ply",
            "block": "bofangqi1",
            "version": "8.1.5",
            "adid": "0",
            "rate": "4,8,16,512,",
            "is_bit64": "1",
            "pps": "0",
        })
        
        # Generate signatures
        timestamp = int(time.time())
        device_id = Signer.DEFAULT_DEVICE_ID
        sign = Signer.generate_sign(params, timestamp)
        qdsf = Signer.generate_qdsf(params, timestamp, device_id)
        
        headers = {
            "User-Agent": Signer.DEFAULT_USER_AGENT,
            "Sign": sign,
            "T": str(timestamp),
            "Qyid": device_id,
            "Qdsf": qdsf,
            "Accept-Encoding": "gzip, deflate, br",
        }
        if cookie_str:
            headers["Cookie"] = cookie_str
        
        try:
            url = "https://api.iq.com/video/play"
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise PlaybackError(f"Failed to resolve mobile playback for tv_id '{tv_id_str}': {e}", code=502)
        
        if data.get("code") != 0:
            raise PlaybackError(f"Mobile playback API error: {data.get('message', 'Unknown error')}", code=502)
        
        # Extract playback data from response
        # The structure may differ from desktop DASH - need to parse video/dash data
        vp = data.get("vp", {})
        dash = data.get("dash", {})
        
        if not (vp or dash):
            raise PlaybackError(f"No playback data in mobile response for tv_id '{tv_id_str}'", code=404)
        
        # Extract streams from vp (video array) or dash structure
        streams: List[StreamQuality] = []
        
        # Parse VP structure if available
        if vp:
            for v in vp if isinstance(vp, list) else [vp]:
                bid = v.get("bid", 500)
                quality_label = BID_MAP.get(bid, f"{bid}p")
                url_data = v.get("url")
                if url_data:
                    stream_url = url_data[0] if isinstance(url_data, list) else url_data
                    streams.append(StreamQuality(
                        quality=quality_label,
                        bid=bid,
                        format="m3u8" if ".m3u8" in str(stream_url) else "ts",
                        url=stream_url,
                        is_vip=False
                    ))
        
        # Parse DASH structure if available
        if dash:
            program = dash.get("program", {})
            for v in program.get("video", []):
                bid = v.get("bid", 500)
                quality_label = BID_MAP.get(bid, f"{bid}p")
                m3u8_text = v.get("m3u8")
                if m3u8_text and isinstance(m3u8_text, str):
                    stream_url = f"/api/play/{tv_id_str}/stream/{bid}.m3u8"
                    self._m3u8_cache[(tv_id_str, bid)] = m3u8_text
                else:
                    ts_url = v.get("play", {}).get("ts", {}).get("l")
                    stream_url = ts_url or f"/api/play/{tv_id_str}/stream/{bid}.m3u8"
                
                streams.append(StreamQuality(
                    quality=quality_label,
                    bid=bid,
                    format="m3u8" if ".m3u8" in str(stream_url) else "ts",
                    url=stream_url,
                    is_vip=False
                ))
        
        if not streams:
            raise PlaybackError(f"No playable streams found for short drama tv_id '{tv_id_str}'", code=404)
        
        streams.sort(key=lambda s: s.bid, reverse=True)
        
        # Extract subtitles
        subtitles: List[SubtitleItem] = []
        dstl = dash.get("dstl", "http://meta.video.iqiyi.com").rstrip("/") if dash else "http://meta.video.iqiyi.com"
        if dash:
            for s in dash.get("program", {}).get("stl", []):
                lid = s.get("lid")
                lang_name, lang_code = LID_MAP.get(lid, (s.get("_name", "Unknown"), "unknown"))
                if s.get("webvtt"):
                    subtitles.append(SubtitleItem(
                        language=lang_name,
                        lang_code=lang_code,
                        format="webvtt",
                        url=f"{dstl}/{s['webvtt'].lstrip('/')}"
                    ))
                if s.get("srt"):
                    subtitles.append(SubtitleItem(
                        language=lang_name,
                        lang_code=lang_code,
                        format="srt",
                        url=f"{dstl}/{s['srt'].lstrip('/')}"
                    ))
        
        # Extract audio tracks
        audio_tracks: List[AudioTrackItem] = []
        seen_audio = set()
        if dash:
            for a in dash.get("program", {}).get("audio", []):
                lid = a.get("lid")
                name = a.get("name", "Original")
                _, lang_code = LID_MAP.get(lid, (name, "zh"))
                key = (name, lang_code)
                if key not in seen_audio:
                    seen_audio.add(key)
                    audio_tracks.append(AudioTrackItem(
                        name=name,
                        lang_code=lang_code,
                        is_default=bool(a.get("_selected", False))
                    ))
        
        duration = 0
        if vp:
            for v in vp if isinstance(vp, list) else [vp]:
                dur = v.get("duration", 0)
                if dur and dur > duration:
                    duration = dur
        
        return PlaybackData(
            tv_id=tv_id_str,
            album_id=album_id_str if album_id_str else None,
            duration=int(duration),
            is_vip_applied=False,
            streams=streams,
            subtitles=subtitles,
            audio_tracks=audio_tracks
        )

    def _resolve_playback(self, tv_id: str, bid_filter: Optional[int] = None) -> PlaybackData:
        """
        Synchronously resolve upstream iQIYI playback dispatch, extracting CDN streams, subtitles, and audio tracks.
        
        Args:
            tv_id: Unique episode item identifier
            bid_filter: Optional bitrate ID filter
            
        Returns:
            PlaybackData object
            
        Raises:
            PlaybackError: If episode is invalid, missing, or upstream resolution fails.
        """
        if not tv_id or not str(tv_id).strip():
            raise PlaybackError("Invalid or missing tv_id", code=400)
            
        tv_id_str = str(tv_id).strip()
        session = self.get_active_session()
        cookie_str = self.get_auth_cookie()
        is_vip = bool(session and session.get("vip_status"))
        
        client = self._get_http_client()
        
        # 1. Fetch play data to get album_id
        play_url = "https://api.iq.com/api/play_data"
        params = self._get_common_params()
        params.update({
            "type": "vertical_play_page",
            "tv_id": tv_id_str,
            "fetch_all": "true",
        })
        headers = Signer.build_headers()
        if cookie_str:
            headers["Cookie"] = cookie_str
            
        try:
            resp = client.get(play_url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json().get("data", {}) or {}
        except Exception as e:
            raise PlaybackError(f"Failed to query play metadata for tv_id '{tv_id_str}': {e}", code=502)
            
        pv = data.get("playing_video") or {}
        album_id = str(pv.get("album_id") or "")
        
        # 2. Look up episode playLocSuffix
        suffix = None
        duration = pv.get("duration") or 0
        if album_id:
            try:
                ep_url = f"https://pcw-api.iq.com/api/episodeListSource/{album_id}"
                ep_params = {
                    "platformId": "3",
                    "modeCode": "intl",
                    "langCode": "en_us",
                    "endOrder": "200",
                    "startOrder": "1",
                }
                ep_res = client.get(ep_url, params=ep_params)
                if ep_res.status_code == 200:
                    epg = ep_res.json().get("data", {}).get("epg", []) or []
                    target = next((e for e in epg if str(e.get("qipuId")) == tv_id_str), None)
                    if target:
                        suffix = target.get("playLocSuffix", "").split("?")[0]
                        if not duration:
                            duration = target.get("len", 0)
            except Exception:
                pass
                
        if not suffix:
            h5_link = data.get("share", {}).get("h5_link", "")
            if h5_link:
                cand = h5_link.split("?")[0].rstrip("/").split("/")[-1]
                if cand and not cand.isdigit():
                    suffix = cand

        if not suffix or suffix.isdigit():
            raise PlaybackError(
                f"No playable URL slug available for episode '{tv_id_str}'. The video may be unreleased (Coming Soon) or unavailable in this region.",
                code=404,
            )

        # 3. Request play page to obtain __NEXT_DATA__ dispatch
        page_url = f"https://www.iq.com/play/{suffix}"
        desktop_ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        req_headers = {
            "User-Agent": desktop_ua,
        }
        
        target_bid = bid_filter if bid_filter is not None else (500 if is_vip else 600)
        cookie_parts = [str(cookie_str)] if cookie_str and isinstance(cookie_str, str) else []
        cookie_parts.append(f"QiyiPlayerBID={target_bid}")
        req_headers["Cookie"] = "; ".join(cookie_parts)
            
        try:
            page_resp = client.get(page_url, headers=req_headers, follow_redirects=True)
            page_resp.raise_for_status()
        except Exception as e:
            raise PlaybackError(f"Failed to fetch playback dispatch page for tv_id '{tv_id_str}': {e}", code=502)

        start_tag = '<script id="__NEXT_DATA__" type="application/json">'
        if start_tag not in page_resp.text:
            raise PlaybackError(f"Playback dispatch data not found for episode '{tv_id_str}'", code=404)
            
        json_str = page_resp.text.split(start_tag, 1)[1].split("</script>", 1)[0]
        try:
            page_data = json.loads(json_str)
        except Exception as e:
            raise PlaybackError(f"Malformed dispatch data for episode '{tv_id_str}': {e}", code=502)

        # If page redirected to album overview, verify if it is an unreleased coming-soon title
        if "/album/" in str(page_resp.url):
            album_state = page_data.get("props", {}).get("initialState", {}).get("album", {})
            if album_state.get("albumReserveShow", {}).get("flag"):
                raise PlaybackError(
                    f"Episode '{tv_id_str}' belongs to an unreleased drama (Coming Soon / Reservation) and has no playable streams on iQIYI yet.",
                    code=404,
                )
            raise PlaybackError(
                f"No playable streams found for episode '{tv_id_str}' (content redirected to album overview).",
                code=404,
            )
            
        dash = (
            page_data.get("props", {}).get("initialProps", {}).get("pageProps", {}).get("prePlayerData", {}).get("dash", {}).get("data")
            or page_data.get("props", {}).get("initialState", {}).get("play", {}).get("prePlayerData", {}).get("dash", {}).get("data")
        )
        if not dash:
            raise PlaybackError(f"Stream dispatch payload empty or restricted for tv_id '{tv_id_str}'", code=404)

        # Check VIP boss paywall status
        boss_not_pass = dash.get("ctl", {}).get("boss_not_pass", False)
        boss_code = dash.get("ctl", {}).get("boss_status_code") or dash.get("boss_ts", {}).get("code")
        boss_msg = dash.get("boss_ts", {}).get("msg") or "Episode is restricted to VIP members"

        program = dash.get("program") or {}
        videos = program.get("video") or []

        if boss_not_pass or boss_code in ["Q00503", "Q00501", "Q00502"] or not videos:
            if boss_not_pass or boss_code:
                raise PlaybackError(
                    f"VIP subscription required to watch this episode ({boss_code or 'VIP_LOCKED'}): {boss_msg}",
                    code=403,
                )
            raise PlaybackError(f"No playable streams found for tv_id '{tv_id_str}'", code=404)

        # 4. Extract streams
        dm = dash.get("dm", "http://meta.video.iqiyi.com")
        streams: List[StreamQuality] = []
        for v in videos:
            v_bid = v.get("bid", 200)
            if bid_filter is not None and v_bid != bid_filter:
                continue
            quality_label = BID_MAP.get(v_bid, f"{v_bid}p")
            m3u8_text = v.get("m3u8")
            if m3u8_text and isinstance(m3u8_text, str) and "#EXTM3U" in m3u8_text:
                self._m3u8_cache[(tv_id_str, v_bid)] = m3u8_text
                stream_url = f"/api/play/{tv_id_str}/stream/{v_bid}.m3u8"
                stream_fmt = "m3u8"
            else:
                ts_url = v.get("play", {}).get("ts", {}).get("l")
                if not ts_url:
                    # Provide local m3u8 stream resolver endpoint
                    stream_url = f"/api/play/{tv_id_str}/stream/{v_bid}.m3u8"
                    stream_fmt = "m3u8"
                else:
                    stream_url = ts_url
                    stream_fmt = "m3u8" if ".m3u8" in ts_url else "ts"
            
            is_stream_vip = v.get("s") == 1 or bool(v.get("vut")) or v_bid >= 600
            streams.append(StreamQuality(
                quality=quality_label,
                bid=v_bid,
                format=stream_fmt,
                url=stream_url,
                is_vip=is_stream_vip
            ))

        streams.sort(key=lambda s: s.bid, reverse=True)

        # 5. Extract subtitles
        dstl = dash.get("dstl", "http://meta.video.iqiyi.com").rstrip("/")
        subtitles: List[SubtitleItem] = []
        for s in dash.get("program", {}).get("stl", []):
            lid = s.get("lid")
            lang_name, lang_code = LID_MAP.get(lid, (s.get("_name", "Unknown"), "unknown"))
            if s.get("webvtt"):
                subtitles.append(SubtitleItem(
                    language=lang_name,
                    lang_code=lang_code,
                    format="webvtt",
                    url=f"{dstl}/{s['webvtt'].lstrip('/')}"
                ))
            if s.get("srt"):
                subtitles.append(SubtitleItem(
                    language=lang_name,
                    lang_code=lang_code,
                    format="srt",
                    url=f"{dstl}/{s['srt'].lstrip('/')}"
                ))

        # 6. Extract audio tracks
        audio_tracks: List[AudioTrackItem] = []
        seen_audio = set()
        for a in dash.get("program", {}).get("audio", []):
            lid = a.get("lid")
            name = a.get("name", "Original")
            _, lang_code = LID_MAP.get(lid, (name, "zh"))
            key = (name, lang_code)
            if key not in seen_audio:
                seen_audio.add(key)
                audio_tracks.append(AudioTrackItem(
                    name=name,
                    lang_code=lang_code,
                    is_default=bool(a.get("_selected", False))
                ))

        if not duration:
            cur_info = page_data.get("props", {}).get("initialState", {}).get("play", {}).get("curVideoInfo", {})
            dur_val = cur_info.get("len")
            if isinstance(dur_val, int):
                duration = dur_val
            elif isinstance(dur_val, str) and ":" in dur_val:
                parts = dur_val.split(":")
                try:
                    if len(parts) == 2:
                        duration = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                except ValueError:
                    duration = 0

        return PlaybackData(
            tv_id=tv_id_str,
            album_id=album_id if album_id else None,
            duration=int(duration),
            is_vip_applied=is_vip,
            streams=streams,
            subtitles=subtitles,
            audio_tracks=audio_tracks
        )

    async def get_playback_short_drama(self, tv_id: str, album_id: str, bid: Optional[int] = None) -> PlaybackData:
        """
        Resolve playback untuk short drama (mobile-exclusive, play_mode: 2).
        
        Args:
            tv_id: Episode tv_id
            album_id: Album/series ID
            bid: Optional bitrate filter
            
        Returns:
            PlaybackData dengan streams + subtitles
        """
        return await asyncio.to_thread(self._resolve_playback_short_drama, tv_id, album_id, bid)

    def _resolve_playback_short_drama(self, tv_id: str, album_id: str, bid_filter: Optional[int] = None) -> PlaybackData:
        """
        Internal resolver untuk short drama via /video/play endpoint.
        """
        from src.client.short_drama_config import MOBILE_PARAMS_BASE, LANGUAGE_TYPE_MAP
        
        tv_id_str = str(tv_id).strip()
        album_id_str = str(album_id).strip()
        
        # Get device info from session or use defaults
        session = self.get_active_session()
        device_id = session.get("device_id") if session else Signer.DEFAULT_DEVICE_ID
        uid = session.get("uid") if session else "0"
        
        # 1. Call /video/play dengan s2=short_ply marker
        url = "https://api.iq.com/video/play"
        
        params = dict(MOBILE_PARAMS_BASE)
        params.update({
            "tv_id": tv_id_str,
            "album_id": album_id_str,
            "qyid": device_id,
            "aqyid": device_id,
            "cupid_id": device_id,
            "cupid_v": "",
            "pu": uid,
            "psp_uid": uid,
        })
        
        # Add timestamp
        params["req_sn"] = str(int(time.time() * 1000))
        params["nano"] = str(int(time.time() * 1000000000) % 1000000000000)
        
        # Generate Sign header
        sign = Signer.generate_video_play_sign(params)
        
        headers = Signer.build_headers(extra_headers={
            "Sign": sign,
        })
        
        # Add auth cookie if available
        cookie = self.get_auth_cookie()
        if cookie and isinstance(cookie, str):
            headers["Cookie"] = cookie
        
        try:
            client = self._get_http_client()
            resp = client.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise PlaybackError(f"Failed to fetch short drama playback: {e}", code=502)
        
        # 2. Parse response
        if not data.get("success"):
            error_info = data.get("error_info", {})
            raise PlaybackError(f"Playback error: {error_info}", code=400)
        
        video = data.get("video", {})
        album = data.get("album", {})
        
        # Extract duration
        duration = video.get("duration", 0)
        
        # 3. Parse subtitles dari subtitle_list
        subtitles: List[SubtitleItem] = []
        tv_pid = video.get("_pid", tv_id_str)
        
        for sub in video.get("subtitle_list", []):
            lang_type = sub.get("language_type")
            make_version = sub.get("make_version", "101")
            
            if lang_type in LANGUAGE_TYPE_MAP:
                lang_name, lang_code = LANGUAGE_TYPE_MAP[lang_type]
            else:
                lang_name = f"Language {lang_type}"
                lang_code = "unknown"
            
            # Construct subtitle URL
            sub_url = f"https://meta.video.iqiyi.com/subtitles/{tv_pid}_{lang_type}.vtt"
            
            subtitles.append(SubtitleItem(
                language=lang_name,
                lang_code=lang_code,
                format="webvtt",
                url=sub_url
            ))
        
        # 4. Streams: placeholder (may need separate /dash call)
        # For now, construct local proxy endpoint
        streams: List[StreamQuality] = []
        for bid_val in [500, 300]:  # Standard qualities
            streams.append(StreamQuality(
                quality=BID_MAP.get(bid_val, f"{bid_val}p"),
                bid=bid_val,
                format="m3u8",
                url=f"/api/play/{tv_pid}/stream/{bid_val}.m3u8",
                is_vip=False
            ))
        
        # 5. Audio tracks
        audio_tracks: List[AudioTrackItem] = [
            AudioTrackItem(name="Original", lang_code="zh", is_default=True)
        ]
        
        return PlaybackData(
            tv_id=tv_id_str,
            album_id=album_id_str,
            duration=int(duration),
            is_vip_applied=False,
            streams=streams,
            subtitles=subtitles,
            audio_tracks=audio_tracks
        )

    async def get_playback(self, tv_id: str, bid: Optional[int] = None) -> PlaybackData:
        """
        Asynchronously resolve playback streams and subtitles for an episode tv_id.
        
        Args:
            tv_id: Unique episode item identifier
            bid: Optional bitrate ID filter (e.g., 500 for 720p, 600 for 1080p)
            
        Returns:
            PlaybackData object containing streams, subtitles, audio tracks, and metadata.
            
        Raises:
            PlaybackError: If episode is invalid, missing, or upstream resolution fails.
        """
        return await asyncio.to_thread(self._resolve_playback, tv_id, bid)

    def _fetch_stream_playlist(self, tv_id: str, bid: int) -> str:
        """
        Synchronously fetch or retrieve cached full HLS M3U8 playlist for a given tv_id and bid.
        """
        tv_id_str = str(tv_id).strip()
        cache_key = (tv_id_str, int(bid))
        if cache_key in self._m3u8_cache:
            return self._m3u8_cache[cache_key]

        # Trigger resolution specifically requesting this bitrate
        self._resolve_playback(tv_id_str, bid_filter=int(bid))
        if cache_key in self._m3u8_cache:
            return self._m3u8_cache[cache_key]

        raise PlaybackError(
            f"HLS playlist not available for tv_id '{tv_id_str}' at bitrate {bid}",
            code=404,
        )

    async def get_stream_playlist(self, tv_id: str, bid: int) -> str:
        """
        Asynchronously get HLS M3U8 playlist for full-duration video playback.
        
        Args:
            tv_id: Unique episode item identifier
            bid: Bitrate ID (e.g., 500 for 720p, 600 for 1080p, 300 for 480p)
            
        Returns:
            Plaintext M3U8 playlist content containing all stream segments with valid CDN tokens.
        """
        return await asyncio.to_thread(self._fetch_stream_playlist, tv_id, bid)

    def is_authenticated(self) -> bool:
        """Check if user has active session."""
        session = self.get_active_session()
        return session is not None and session.get("is_active", False)

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if self._http_client is not None:
            self._http_client.close()
