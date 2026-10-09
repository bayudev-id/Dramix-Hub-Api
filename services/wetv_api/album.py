from fastapi import APIRouter, Query, Request, HTTPException
import httpx
import json
import asyncio


router = APIRouter(prefix="/api/wetv")

# We use the same language mappings as before
LANG_MAPPINGS = {
    "id": ("id", "1491937"),
    "en": ("en", "1491988"),
    "th": ("th", "1491973"),
    "zh": ("zh-tw", "8229847"),  # zh-tw
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



@router.get("/album/{cid}")
async def get_album_details(
    cid: str,
    lang: str = Query("id", description="Language code (id, en, th, zh, vi, ms)")
):
    """
    Fetch album/drama details, its paginated episodes, and dynamic clips.
    """
    lang_info = LANG_MAPPINGS.get(lang.lower(), LANG_MAPPINGS["id"])
    url_lang, lang_code = lang_info
    
    url = f"https://wetv.vip/{url_lang}/album/{cid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": f"{url_lang},en;q=0.9",
        "Cookie": f"lang_code={lang_code}; wetv_lang={url_lang}; country_code=153513",
        "X-Forwarded-For": "114.124.237.218"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # We concurrently fetch the main HTML and page 1 of clips (size=40)
            tasks = [
                client.get(url, headers=headers),
                client.get(f"https://wetv.vip/api/getVideoInfoListByCid?cid={cid}&type=clip&size=40&page=1", headers=headers)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Extract main response
            resp = results[0]
            if isinstance(resp, Exception) or resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch album page from WeTV")
                
            next_data = extract_next_data(resp.text)
            if not next_data:
                raise HTTPException(status_code=500, detail="Failed to parse WeTV SSR data")
                
            page_props = next_data.get("props", {}).get("pageProps", {})
            data = page_props.get("data", {})
            
            cover_info = data.get("coverInfo", {})
            
            # Parse rich cast/actors information (including photos and roles)
            raw_actors = cover_info.get("actors", [])
            cast_list = []
            for act in raw_actors:
                raw_role = act.get("role", "actor")
                cast_list.append({
                    "id": act.get("id"),
                    "name": act.get("name", ""),
                    "avatar": act.get("avatar", ""),
                    "role": raw_role
                })
            
            # Format the output nicely
            album_detail = {
                "cid": cover_info.get("cid", cid),
                "title": cover_info.get("title", ""),
                "description": cover_info.get("description", ""),
                "cast": cast_list,
                "year": cover_info.get("year", ""),
                "area": cover_info.get("areaName", ""),
                "score": cover_info.get("score", ""),
                "genres": cover_info.get("mainGenres", []),
                "total_episodes": cover_info.get("episodeAll", 0),
                "updated_episodes": cover_info.get("episodeUpdated", 0),
                "update_info": cover_info.get("updateInfo", ""),
                "cover_h": cover_info.get("posterHz", ""),
                "cover_v": cover_info.get("posterVt", ""),
                "is_vip": check_is_vip(cover_info)
            }
            
            # Episodes Page 1
            episodes_data = data.get("episodes", {})
            ep_list_raw = episodes_data.get("data", [])
            total_episodes = episodes_data.get("total", 0)
            
            # Clips Page 1
            clips_list_raw = []
            total_clips = 0
            clips_resp = results[1]
            if not isinstance(clips_resp, Exception) and clips_resp.status_code == 200:
                try:
                    clips_data = clips_resp.json()
                    clips_list_raw = clips_data.get("data", [])
                    total_clips = clips_data.get("total", 0)
                except Exception:
                    pass
            
            # Concurrently fetch remaining pages if they exist
            tasks_remaining = []
            episodes_pages_to_fetch = []
            clips_pages_to_fetch = []
            
            # Calculate total pages needed (WeTV max size is 40)
            if total_episodes > len(ep_list_raw):
                total_ep_pages = (total_episodes + 39) // 40
                for p in range(2, total_ep_pages + 1):
                    ep_url = f"https://wetv.vip/api/getVideoInfoListByCid?cid={cid}&type=episode&size=40&page={p}"
                    tasks_remaining.append(client.get(ep_url, headers=headers))
                    episodes_pages_to_fetch.append(p)
                    
            if total_clips > len(clips_list_raw):
                total_clip_pages = (total_clips + 39) // 40
                for p in range(2, total_clip_pages + 1):
                    clip_url = f"https://wetv.vip/api/getVideoInfoListByCid?cid={cid}&type=clip&size=40&page={p}"
                    tasks_remaining.append(client.get(clip_url, headers=headers))
                    clips_pages_to_fetch.append(p)
            
            if tasks_remaining:
                remaining_results = await asyncio.gather(*tasks_remaining, return_exceptions=True)
                
                # Merge episode pages
                for idx, p in enumerate(episodes_pages_to_fetch):
                    res = remaining_results[idx]
                    if not isinstance(res, Exception) and res.status_code == 200:
                        try:
                            ep_list_raw.extend(res.json().get("data", []))
                        except Exception:
                            pass
                            
                # Merge clip pages
                offset = len(episodes_pages_to_fetch)
                for idx, p in enumerate(clips_pages_to_fetch):
                    res = remaining_results[offset + idx]
                    if not isinstance(res, Exception) and res.status_code == 200:
                        try:
                            clips_list_raw.extend(res.json().get("data", []))
                        except Exception:
                            pass
            
            return {
                "status": "success",
                "album": album_detail,
                "episodes": [format_video_item(ep) for ep in ep_list_raw],
                "clips": [format_video_item(c) for c in clips_list_raw]
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@router.get("/album/{cid}/clips")
async def get_album_clips(
    cid: str,
    lang: str = Query("id", description="Language code (id, en, th, zh, vi, ms)"),
    page: int = Query(1, description="Clip page number"),
    size: int = Query(20, description="Number of clips per page")
):
    """
    Fetch exclusive clips, BTS, or trailers for a given album.
    """
    lang_info = LANG_MAPPINGS.get(lang.lower(), LANG_MAPPINGS["id"])
    url_lang, lang_code = lang_info
    
    # WeTV REST API endpoint for clips
    api_url = f"https://wetv.vip/api/getVideoInfoListByCid?cid={cid}&type=clip&size={size}&page={page}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": f"{url_lang},en;q=0.9",
        "Cookie": f"lang_code={lang_code}; wetv_lang={url_lang}; country_code=153513",
        "X-Forwarded-For": "114.124.237.218"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            api_resp = await client.get(api_url, headers=headers)
            if api_resp.status_code != 200:
                raise HTTPException(status_code=api_resp.status_code, detail="Failed to fetch clips from WeTV")
            
            api_data = api_resp.json()
            clip_list = api_data.get("data", [])
            
            return {
                "status": "success",
                "clips": {
                    "total": api_data.get("total", 0),
                    "page": api_data.get("page", page),
                    "has_next": api_data.get("hasNext", False),
                    "list": [format_video_item(clip) for clip in clip_list]
                }
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

