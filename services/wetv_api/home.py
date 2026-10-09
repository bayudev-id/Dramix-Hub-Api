from fastapi import APIRouter, HTTPException, Query, Header
import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import quote, parse_qs
from bs4 import BeautifulSoup
import json

router = APIRouter(prefix="/api/wetv", tags=["WeTV Home & Content"])

# Mappings of channels/tabs
CATEGORIES = [
    {"id": "1001", "name": "Untukmu"},
    {"id": "10336", "name": "Mini Series💘"},
    {"id": "10003", "name": "Indonesia"},
    {"id": "10054", "name": "Mandarin"},
    {"id": "10022", "name": "Anime 🕹️"},
    {"id": "10473", "name": "Micro Drama"},
    {"id": "10077", "name": "Korea"},
    {"id": "10108", "name": "Kolosal"},
    {"id": "10096", "name": "VarShow"},
    {"id": "10062", "name": "Film"},
    {"id": "10325", "name": "Anak"}
]

# Supported language codes mapping to WeTV parameter keys
LANG_MAPPINGS = {
    "en": {"code": "1491988", "accept_lang": "en-US,en;q=0.9"},
    "th": {"code": "1491973", "accept_lang": "th-TH,th;q=0.9,en;q=0.8"},
    "zh-tw": {"code": "8229847", "accept_lang": "zh-TW,zh;q=0.9"},
    "zh-cn": {"code": "1491963", "accept_lang": "zh-CN,zh;q=0.9"},
    "id": {"code": "1491937", "accept_lang": "id-ID,id;q=0.9,en;q=0.8"},
    "hi": {"code": "35", "accept_lang": "hi-IN,hi;q=0.9,en;q=0.8"},
    "ja": {"code": "8", "accept_lang": "ja-JP,ja;q=0.9"},
    "ko": {"code": "9", "accept_lang": "ko-KR,ko;q=0.9"},
    "pt": {"code": "12", "accept_lang": "pt-BR,pt;q=0.9"},
    "es": {"code": "14", "accept_lang": "es-ES,es;q=0.9"},
    "ar": {"code": "54", "accept_lang": "ar-AE,ar;q=0.9"},
    "vi": {"code": "1491994", "accept_lang": "vi-VN,vi;q=0.9"},
    "ms": {"code": "40", "accept_lang": "ms-MY,ms;q=0.9"}
}

# List of languages for mapping response
LANGUAGES = [
    {"id": "id", "name": "Bahasa Indonesia"},
    {"id": "en", "name": "English"},
    {"id": "pt", "name": "Português"},
    {"id": "es", "name": "Español"},
    {"id": "th", "name": "ไทย"},
    {"id": "vi", "name": "Tiếng Việt"},
    {"id": "ms", "name": "Bahasa Melayu"},
    {"id": "ja", "name": "日本語"},
    {"id": "ko", "name": "한국어"},
    {"id": "zh-cn", "name": "简体中文"},
    {"id": "zh-tw", "name": "繁體中文"},
    {"id": "hi", "name": "हिन्दी"},
    {"id": "ar", "name": "العربية"}
]

def generate_gtk(vusession: str) -> int:
    """Generate CSRF/gtk token from session key."""
    if not vusession:
        return 0
    t = 5381
    for char in vusession:
        t = (t + (t << 5) + ord(char)) & 0xFFFFFFFF
    return 2147483647 & t

def get_page_ctx(channel_id: str, page_no: int) -> str:
    """Generate context string for pagination dynamically."""
    chtype = "5" if channel_id == "1001" else "0"
    mod_start = (page_no - 1) * 4
    mod_end = page_no * 4
    
    # WeTV URL encodes the page_data_ctx inside pageCtx
    page_data_ctx = f"chid=&mod_no={mod_start}&mod_size=4&page_no=0&page_size=30&mod={mod_start}-{mod_end}&all_mod_count=18"
    encoded_page_data_ctx = quote(page_data_ctx)
    
    ctx = f"chid={channel_id}&chtype={chtype}&cms_chid={channel_id}&page_no={page_no}&mod_no=0&item_no=0&page_data_ctx={encoded_page_data_ctx}"
    return ctx

@router.get("/sections")
async def get_sections():
    """Get list of predefined WeTV sections from sections.json."""
    import os
    from datetime import datetime, timezone
    
    file_path = os.path.join(os.path.dirname(__file__), "sections.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Update timestamp to current time for freshness
            data["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membaca sections.json: {str(e)}")

@router.get("/categories")
async def get_categories():
    """Get list of WeTV home categories/channels."""
    return {
        "status": "success",
        "data": CATEGORIES
    }

@router.get("/languages")
async def get_languages():
    """Get list of supported languages."""
    return {
        "status": "success",
        "data": LANGUAGES
    }

@router.get("/channel/{channel_id}")
async def get_channel_data_path(
    channel_id: str,
    page_no: int = Query(1, ge=1, description="Nomor halaman/paging"),
    lang: str = Query("id", description="Kode bahasa (e.g. id, en, pt, th)"),
    module_index: Optional[int] = Query(None, description="Filter index modul tertentu")
):
    """Retrieve WeTV channel data using path parameter."""
    return await get_channel_data(channel_id=channel_id, page_no=page_no, lang=lang, module_index=module_index)

def format_cms_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format WeTV CMS items into a standard structure."""
    formatted_items = []
    for item in items:
        # Determine cover image URL
        cover_url = item.get("pic")
        
        # Extract vertical and horizontal cover options from img_list
        img_list = item.get("img_list") or {}
        cover_v = img_list.get("img_v") or cover_url
        cover_h = img_list.get("img_h") or cover_url
        
        # Parse tags and VIP status
        tags = []
        is_vip = False
        episode_info = ""
        
        tag_label_list = item.get("tag_label_list")
        if tag_label_list:
            for tag in tag_label_list:
                text = tag.get("text")
                if text:
                    tags.append(text)
                    if "VIP" in text or tag.get("label_type") == "UI_FUNCTION_LABEL_TYPE_PAY":
                        is_vip = True
                        
        mark_label_list = item.get("mark_label_list")
        if mark_label_list:
            for k, mark in mark_label_list.items():
                text = mark.get("text")
                if text:
                    if "EP" in text or "Total" in text:
                        episode_info = text
                    else:
                        tags.append(text)
                        if "VIP" in text or "Sewa" in text:
                            is_vip = True
        
        formatted_items.append({
            "id": item.get("id") or item.get("cid"),
            "cid": item.get("cid"),
            "title": item.get("title") or item.get("main_title"),
            "subtitle": item.get("subtitle") or item.get("sub_title"),
            "cover": cover_url,
            "cover_v": cover_v,
            "cover_h": cover_h,
            "episode_info": episode_info,
            "tags": list(set(tags)), # unique values
            "is_vip": is_vip,
            "score": item.get("film_score") or 0
        })
    return formatted_items

def resolve_custom_channel(channel_id: str) -> tuple[str, Optional[int], Optional[int]]:
    """
    Given a custom channel_id like '10054933', resolves it to base channel '10054',
    page_no 9, and module_index 33.
    Returns (base_channel_id, page_no, module_index).
    """
    base_ids = [cat["id"] for cat in CATEGORIES]
    # Sort by length descending to match longest prefix first
    base_ids.sort(key=len, reverse=True)
    
    for bid in base_ids:
        if channel_id.startswith(bid):
            if len(channel_id) == len(bid):
                return bid, None, None
            
            L = len(bid)
            try:
                page_no = int(channel_id[L])
                module_index = int(channel_id[L+1:])
                return bid, page_no, module_index
            except (ValueError, IndexError):
                pass
                
    return channel_id, None, None

@router.get("/channel")
async def get_channel_data(
    channel_id: str = Query("1001", description="ID kategori WeTV (e.g. 1001, 10003)"),
    page_no: int = Query(1, ge=1, description="Nomor halaman/paging"),
    lang: str = Query("id", description="Kode bahasa (e.g. id, en, pt, th)"),
    module_index: Optional[int] = Query(None, description="Filter index modul tertentu")
):
    """Retrieve and format WeTV homepage channel data (banner, lists, categories)."""
    original_channel_id = channel_id
    base_channel, resolved_page, resolved_idx = resolve_custom_channel(channel_id)
    if resolved_page is not None:
        page_no = resolved_page
    if resolved_idx is not None:
        module_index = resolved_idx
    channel_id = base_channel
    # Resolve language mapping
    lang_info = LANG_MAPPINGS.get(lang.lower(), LANG_MAPPINGS["id"])
    
    # CASE 1: Page 1 - Try scraping SSR HTML __NEXT_DATA__ first for exact desktop layout
    if page_no == 1:
        try:
            # WeTV URL structure for channels
            url = f"https://wetv.vip/{lang.lower()}/channel/{channel_id}?id={channel_id}&type=PAGE_TYPE_MODULE_LIST"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": lang_info["accept_lang"],
                "X-Forwarded-For": "114.124.237.218" # Force Indonesia IP
            }
            cookies = {
                "wetv_lang": lang.lower(),
                "lang_code": lang_info["code"],
                "country_code": "153513"
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, cookies=cookies, timeout=10)
                if resp.status_code == 200:
                    html_text = resp.text
                    start_tag = 'id="__NEXT_DATA__"'
                    start_pos = html_text.find(start_tag)
                    next_data = None
                    if start_pos != -1:
                        content_start = html_text.find('>', start_pos) + 1
                        content_end = html_text.find('</script>', content_start)
                        json_str = html_text[content_start:content_end]
                        next_data = json.loads(json_str)
                        
                    if next_data:
                        page_props = next_data.get("props", {}).get("pageProps", {})
                        modules = page_props.get("data", {}).get("modules", [])
                        
                        formatted_modules = []
                        for idx, mod in enumerate(modules):
                            items = mod.get("items", [])
                            if not items:
                                continue
                            
                            mod_title = None
                            block_info = mod.get("block_info", {})
                            if block_info:
                                mod_title = block_info.get("title")
                            if not mod_title:
                                mod_title = mod.get("name") or mod.get("title") or f"Rekomendasi {idx+1}"
                                
                            formatted_items = format_cms_items(items)
                            if formatted_items:
                                formatted_modules.append({
                                    "module_index": idx,
                                    "module_title": mod_title,
                                    "items_count": len(formatted_items),
                                    "items": formatted_items
                                })
                                
                        # Filter by module_index if specified
                        if module_index is not None:
                            formatted_modules = [m for m in formatted_modules if m.get("module_index") == module_index]
                            
                        return {
                            "status": "success",
                            "channel_id": original_channel_id,
                            "page_no": page_no,
                            "data": formatted_modules
                        }
        except Exception:
            # Fallback to standard API on any scraping exception
            pass

    # CASE 2: Fallback / Page > 1 - Query WeTV REST API
    ctx = get_page_ctx(channel_id, page_no)
    url = f"https://wetv.vip/api/channel?id={channel_id}&pageCtx={quote(ctx)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": lang_info["accept_lang"],
        "Referer": f"https://wetv.vip/{lang.lower()}",
        "Origin": "https://wetv.vip",
        "X-Forwarded-For": "114.124.237.218" # Force Indonesia IP
    }
    
    cookies = {
        "wetv_lang": lang.lower(),
        "lang_code": lang_info["code"],
        "country_code": "153513"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, cookies=cookies, timeout=10)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Gagal mengambil data dari WeTV API")
                
            json_data = resp.json()
            if json_data.get("retCode") != 0:
                raise HTTPException(status_code=400, detail=f"WeTV API error: {json_data.get('error')}")
                
            raw_modules = json_data.get("response", {}).get("modules", [])
            formatted_modules = []
            
            mod_start = (page_no - 1) * 4
            for idx, mod in enumerate(raw_modules):
                items = mod.get("items", [])
                if not items:
                    continue
                
                mod_title = None
                block_info = mod.get("block_info", {})
                if block_info:
                    mod_title = block_info.get("title")
                if not mod_title:
                    mod_title = mod.get("name") or mod.get("title") or f"Rekomendasi {mod_start + idx + 1}"
                
                formatted_items = format_cms_items(items)
                if formatted_items:
                    formatted_modules.append({
                        "module_index": mod_start + idx,
                        "module_title": mod_title,
                        "items_count": len(formatted_items),
                        "items": formatted_items
                    })
            
            # Filter by module_index if specified
            if module_index is not None:
                formatted_modules = [m for m in formatted_modules if m.get("module_index") == module_index]
                
            return {
                "status": "success",
                "channel_id": original_channel_id,
                "page_no": page_no,
                "data": formatted_modules
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Kesalahan koneksi ke WeTV API: {str(e)}")



