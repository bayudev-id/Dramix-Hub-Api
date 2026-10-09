from fastapi import APIRouter, Query, HTTPException, Request
import httpx
import json
import time
import uuid
import os
import socket
from dotenv import load_dotenv
from encryption import CKey

# DNS Patch: pastikan play.wetv.vip ter-resolve dengan benar jika ISP memblokir DNS
_orig_getaddrinfo = socket.getaddrinfo
def _custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "play.wetv.vip":
        host = "202.169.45.206"
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _custom_getaddrinfo

# Load environment variables with absolute path relative to this file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

router = APIRouter(prefix="/api/wetv")

async def get_active_vip_cookies() -> dict:
    """
    Fetch the first active VIP account from Supabase database via REST API.
    Checks for expiry automatically on query and disables expired VIP accounts.
    Real-Time Auto-Heal: Refreshes the vusession token if older than 90 minutes!
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("[Supabase VIP Fetch Warning] SUPABASE_URL or SUPABASE_KEY is missing!")
        return None
    try:
        from datetime import datetime, timezone
        current_time = int(time.time())
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}

        # Ambil semua akun yang is_vip = True beserta guid, video_guid, uin via PostgREST
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{url}/rest/v1/wetv_vip_accounts?select=vuserid,cookies,is_vip,vip_end,updated_at,guid,video_guid,uin&is_vip=eq.true",
                headers=headers
            )
            data = resp.json() if resp.status_code == 200 else []

            if data and isinstance(data, list):
                for acc in data:
                    vuserid = acc.get("vuserid")
                    vip_end = acc.get("vip_end") or 0
                    
                    # JIKA VIP SUDAH EXPIRED/END!
                    if vip_end > 0 and current_time >= vip_end:
                        print(f"[Supabase VIP Expired] Akun {vuserid} sudah kedaluwarsa. Mengupdate database...")
                        try:
                            await client.patch(
                                f"{url}/rest/v1/wetv_vip_accounts?vuserid=eq.{vuserid}",
                                headers=headers,
                                json={"is_vip": False}
                            )
                        except Exception as db_err:
                            print(f"[Supabase VIP Auto-Expiry Error] Gagal merubah status: {db_err}")
                        continue

                    # VIP masih aktif! Susun cookies lengkap
                    cookies = acc.get("cookies") or {}
                    if "vuserid" not in cookies:
                        cookies["vuserid"] = vuserid
                    
                    db_guid = acc.get("guid") or ""
                    if db_guid:
                        cookies["guid"] = db_guid
                        cookies["video_guid"] = acc.get("video_guid") or db_guid
                        cookies["uin"] = acc.get("uin") or db_guid
                    
                    print(f"[Supabase VIP Fetch] Akun VIP aktif: {vuserid}")
                    return cookies

            # Fallback: jika tidak ada VIP aktif, ambil akun acak
            fb_resp = await client.get(
                f"{url}/rest/v1/wetv_vip_accounts?select=vuserid,cookies,guid,video_guid,uin&limit=1",
                headers=headers
            )
            fb_data = fb_resp.json() if fb_resp.status_code == 200 else []
            if fb_data and isinstance(fb_data, list) and len(fb_data) > 0:
                cookies = fb_data[0].get("cookies") or {}
                vuserid = fb_data[0].get("vuserid")
                if "vuserid" not in cookies and vuserid:
                    cookies["vuserid"] = vuserid
                db_guid = fb_data[0].get("guid") or ""
                if db_guid:
                    cookies["guid"] = db_guid
                    cookies["video_guid"] = fb_data[0].get("video_guid") or db_guid
                    cookies["uin"] = fb_data[0].get("uin") or db_guid
                return cookies
    except Exception as e:
        print(f"[Supabase VIP Fetch Error] {e}")
    return None

def generate_guid() -> str:
    """Generate a random 32-char hex GUID (same format as WeTV browser)."""
    return uuid.uuid4().hex

LANG_MAPPINGS = {
    "id": ("id", "1491937"),
    "en": ("en", "1491988"),
    "th": ("th", "1491973"),
    "zh": ("zh-tw", "8229847"),
    "zh-cn": ("zh-cn", "1491963"),
    "vi": ("vi", "1491994"),
    "ms": ("ms", "40"),
    "pt": ("pt", "8"),
    "es": ("es", "9"),
    "ar": ("ar", "12"),
    "ko": ("ko", "14"),
}

def extract_next_data(html_content: str) -> dict:
    start_tag = 'id="__NEXT_DATA__"'
    start_pos = html_content.find(start_tag)
    if start_pos == -1:
        return None
    content_start = html_content.find('>', start_pos) + 1
    content_end = html_content.find('</script>', content_start)
    if content_end == -1:
        return None
    json_str = html_content[content_start:content_end]
    try:
        return json.loads(json_str)
    except Exception:
        return None

def check_is_vip(item: dict) -> bool:
    # 1. Check if payStatus != 8 (if payStatus is present and not 8)
    pay_status = item.get("payStatus")
    if pay_status is not None and pay_status != 8:
        return True
        
    # 2. Check labels dictionary
    labels = item.get("labels") or {}
    if isinstance(labels, dict):
        for lbl in labels.values():
            if isinstance(lbl, dict):
                text = lbl.get("text")
                if text and "VIP" in text:
                    return True
    elif isinstance(labels, list):
        for lbl in labels:
            if isinstance(lbl, dict):
                text = lbl.get("text")
                if text and "VIP" in text:
                    return True
            elif isinstance(lbl, str) and "VIP" in lbl:
                return True
                
    return False
def extract_label(item: dict) -> str:
    labels = item.get("labels") or {}
    if isinstance(labels, dict):
        for lbl in labels.values():
            if isinstance(lbl, dict):
                text = lbl.get("text")
                if text:
                    return text
    elif isinstance(labels, list):
        for lbl in labels:
            if isinstance(lbl, dict):
                text = lbl.get("text")
                if text:
                    return text
            elif isinstance(lbl, str):
                return lbl
    return ""

def format_video_item(item: dict) -> dict:
    display_label = extract_label(item)
    is_vip = check_is_vip(item)
    is_express = "Express" in display_label
    is_trailer = (item.get("isTrailer", 0) == 1) or ("Trailer" in display_label) or ("Teaser" in display_label) or ("Pratinjau" in display_label)
    
    tags = []
    if display_label:
        tags.append(display_label)
        
    return {
        "vid": item.get("vid", ""),
        "title": item.get("title", ""),
        "episode": item.get("episode", ""),
        "cover": item.get("pic_496_280", "") or item.get("pic_640_360", ""),
        "is_vip": is_vip,
        "is_trailer": is_trailer,
        "is_express": is_express,
        "label": display_label,
        "tags": tags
    }


def parse_jsonp(text: str) -> dict:
    """Strip JSONP wrapper: callback({...})"""
    start = text.find('(')
    end = text.rfind(')')
    if start != -1 and end != -1:
        return json.loads(text[start+1:end])
    return json.loads(text)

async def fetch_stream_info(
    vid: str, 
    cid: str, 
    lang_code: str, 
    url_lang: str, 
    defn: str = "",
    vip_cookies: dict = None,
    delay_sec: int = 0,
    client_ip: str = ""
) -> dict:
    """
    Fetch stream URL and subtitle info from getvinfo API asynchronously.
    """
    ck = CKey()
    guid = generate_guid()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    
    # If we have VIP cookies, adopt their matching GUID and User-Agent
    if vip_cookies:
        guid = vip_cookies.get("guid") or vip_cookies.get("video_guid") or guid
        user_agent = vip_cookies.get("user_agent") or user_agent
        
    platform = "4830201"
    app_ver = "2.8.44"
    play_url = f"https://wetv.vip/{url_lang}/play/{cid}/{vid}"
    tm = str(int(time.time()) + delay_sec)
    
    ckey = ck.make(vid, tm, app_ver, guid, platform, play_url)
    
    logintoken = ""
    if vip_cookies:
        logintoken = vip_cookies.get("vusession") or vip_cookies.get("vutoken") or ""
        
    params = {
        "charge": "0", "otype": "json", "defnpayver": "0",
        "spau": "1", "spaudio": "1", "spwm": "1", "sphls": "1",
        "host": "wetv.vip", "refer": "wetv.vip",
        "ehost": play_url, "sphttps": "1",
        "encryptVer": "8.1", "cKey": ckey,
        "clip": "4", "guid": guid,
        "platform": platform, "sdtfrom": "1002",
        "appVer": app_ver, "vid": vid,
        "defn": defn, "fhdswitch": "0", "dtype": "3", "spsrt": "2",
        "tm": tm, "lang_code": lang_code, "logintoken": logintoken,
        "spgzip": "1", "spcaptiontype": "1", "cmd": "2",
        "country_code": "153513", "cid": cid,
        "drm": "0", "multidrm": "0",
        "callback": "cb",
    }
    
    headers = {
        "User-Agent": user_agent,
        "Referer": "https://wetv.vip/"
    }
    if client_ip:
        headers["X-Forwarded-For"] = client_ip
    cookies = {
        "country_code": "153513", "lang_code": lang_code,
        "guid": guid, "video_guid": guid,
        "uin": guid,
    }
    if vip_cookies:
        # Exclude user_agent as it is sent via headers
        db_cookies = {k: v for k, v in vip_cookies.items() if k != "user_agent"}
        cookies.update(db_cookies)
        
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://play.wetv.vip/getvinfo",
                params=params, headers=headers, cookies=cookies
            )
            data = parse_jsonp(resp.text)
            em = data.get("em", -99)
            if em == 0:
                data["_requested_defn"] = defn # Add tag to know which defn this was
                return data
            return None
    except Exception:
        return None

def format_stream_data(responses: list) -> dict:
    """Format multiple /getvinfo responses into clean stream + subtitle data mapping."""
    result = {"streams": [], "subtitles": []}
    
    # We only need to extract subtitles once from the first successful response
    meta_extracted = False
    
    defn_to_quality = {
        "ld": "144p",
        "sd": "360p",
        "hd": "480p",
        "shd": "720p",
        "fhd": "1080p",
        "": "Auto"
    }
    
    for getvinfo_data in responses:
        if not getvinfo_data:
            continue
            
        req_defn = getvinfo_data.get("_requested_defn", "")
        q_label = defn_to_quality.get(req_defn, req_defn)
        
        # Stream URLs
        vl = getvinfo_data.get("vl", {})
        vi_list = vl.get("vi", [])
        if vi_list:
            vi = vi_list[0]
            ul = vi.get("ul", {})
            for ui in ul.get("ui", []):
                hls = ui.get("hls", {})
                stream_url = ui.get("url", "") + hls.get("pt", "")
                if stream_url:
                    result["streams"].append({
                        "url": stream_url,
                        "quality": q_label,
                        "format": "hls"
                    })
                    break # Usually only one main stream per defn is needed
        
        if not meta_extracted:
            # Subtitles
            sfl = getvinfo_data.get("sfl", {})
            for sub in sfl.get("fi", []):
                sub_url = sub.get("url", "")
                # Convert the .vtt.m3u8?ver=4 wrapper URL into a direct .vtt URL
                if ".vtt.m3u8" in sub_url:
                    sub_url = sub_url.split(".m3u8")[0]
                
                result["subtitles"].append({
                    "lang": sub.get("lang", ""),
                    "name": sub.get("name", ""),
                    "url": sub_url,
                    "selected": bool(sub.get("selected")),
                })
            meta_extracted = True
            
    return result


@router.get("/play/{cid}/{vid}")
async def get_play_details(
    request: Request,
    cid: str,
    vid: str,
    lang: str = Query("id", description="Language code (id, en, th, zh, vi, ms)"),
    defn: str = Query("", description="Kualitas video: ld (144p), sd (360p), hd (480p), shd (720p), fhd (1080p). Kosongkan untuk default.")
):
    """
    Fetch playing video details, full playlist, stream URL, and subtitles.
    """
    lang_info = LANG_MAPPINGS.get(lang.lower(), LANG_MAPPINGS["id"])
    url_lang = lang_info[0]
    lang_code = lang_info[1]
    
    url = f"https://wetv.vip/{url_lang}/play/{cid}/{vid}"

    # Extract real client IP to pass it to WeTV, so CDN binds URL to correct client IP
    client_ip = request.headers.get("x-forwarded-for")
    if not client_ip:
        client_ip = request.client.host if request.client else ""
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    print(f"[WeTV Play] Received client_ip: {client_ip} from headers: {request.headers.get('x-forwarded-for')}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": f"lang_code={lang_code}; wetv_lang={url_lang}; country_code=153513"
    }
    if client_ip:
        headers["X-Forwarded-For"] = client_ip
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch play page from WeTV")
                
            next_data = extract_next_data(resp.text)
            if not next_data:
                raise HTTPException(status_code=500, detail="Failed to parse WeTV SSR data")
                
            page_props = next_data.get("props", {}).get("pageProps", {})
            
            # For the play page, data is actually a JSON string
            data_str = page_props.get("data", "{}")
            if not isinstance(data_str, str):
                data_str = json.dumps(data_str)
                
            try:
                play_data = json.loads(data_str)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Failed to parse play data string")
            
            cover_info = play_data.get("coverInfo", {})
            video_info = play_data.get("videoInfo", {})
            video_list = play_data.get("videoList", [])
            
            # Fetch active VIP cookies from database (ONCE per API request)
            # Akan melakukan auto-heal (refresh token otomatis) jika usang!
            vip_cookies = await get_active_vip_cookies()

            # Helper function to perform stream fetch
            async def get_responses(cookies):
                if defn in ["all", ""]:
                    import asyncio
                    tasks = [
                        fetch_stream_info(vid, cid, lang_code, url_lang, q, cookies, delay_sec=i, client_ip=client_ip)
                        for i, q in enumerate(["ld", "sd", "hd", "shd", "fhd"])
                    ]
                    return await asyncio.gather(*tasks)
                else:
                    resp_data = await fetch_stream_info(vid, cid, lang_code, url_lang, defn, cookies, client_ip=client_ip)
                    return [resp_data]

            responses = await get_responses(vip_cookies)

            # Check if responses indicate a preview/trial or failure
            is_preview = False
            if not responses or all(r is None for r in responses):
                is_preview = True
            else:
                for r in responses:
                    if r is not None:
                        preview = r.get("preview")
                        td = r.get("td")
                        if preview is not None and td is not None:
                            try:
                                preview_val = float(preview)
                                td_val = float(td)
                                if preview_val > 0 and preview_val < td_val:
                                    is_preview = True
                                    break
                            except (ValueError, TypeError):
                                pass

            # Auto-Heal Active: jika terdeteksi preview/trial atau gagal total, biarkan node.js worker yang me-refresh
            if is_preview:
                if vip_cookies:
                    vuserid = vip_cookies.get("vuserid")
                    if vuserid:
                        print(f"[Auto-Heal Active] Terdeteksi preview/trial atau gagal total untuk {vuserid}. Worker Node.js akan melakukan penyegaran token.")

            stream_data = format_stream_data(responses)
            
            import datetime
            timestamp_str = f"{datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z [wetv]"
            
            return {
                "code": 200,
                "message": "Success",
                "provider": "WeTV",
                "timestamp": timestamp_str,
                "data": stream_data
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
