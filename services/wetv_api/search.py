from fastapi import APIRouter, HTTPException, Query
import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import quote
import json
from home import LANG_MAPPINGS

router = APIRouter(prefix="/api/wetv", tags=["WeTV Search"])

@router.get("/search")
async def search_drama(
    query: str = Query(..., description="Kata kunci pencarian"),
    page_no: int = Query(1, ge=1, description="Nomor halaman/paging"),
    lang: str = Query("id", description="Kode bahasa (e.g. id, en, pt, th)")
):
    """Search for dramas on WeTV (with pagination and language support)."""
    lang_info = LANG_MAPPINGS.get(lang.lower(), LANG_MAPPINGS["id"])
    
    # WeTV search URL pattern
    # Format: https://wetv.vip/{lang}/search/{query}?cur={page_no}
    url = f"https://wetv.vip/{lang.lower()}/search/{quote(query)}?cur={page_no}"
    
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
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, cookies=cookies, timeout=10)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Gagal mencari data dari WeTV")
                
            html_text = resp.text
            start_tag = 'id="__NEXT_DATA__"'
            start_pos = html_text.find(start_tag)
            
            if start_pos == -1:
                raise HTTPException(status_code=502, detail="Gagal menemukan data pencarian (struktur HTML berubah)")
                
            content_start = html_text.find('>', start_pos) + 1
            content_end = html_text.find('</script>', content_start)
            json_str = html_text[content_start:content_end]
            next_data = json.loads(json_str)
            
            page_props = next_data.get("props", {}).get("pageProps", {})
            search_data = page_props.get("data", {})
            result = search_data.get("result", [])
            
            # Formatting results
            formatted_results = []
            for item in result:
                tags = []
                is_vip = False
                
                # Extract labels
                labels = item.get("labels") or {}
                for k, lbl in labels.items():
                    txt = lbl.get("text")
                    if txt:
                        tags.append(txt)
                        if "VIP" in txt:
                            is_vip = True
                            
                # Extract genres
                genres = item.get("mainGenres") or []
                for g in genres:
                    tags.append(g)
                sub_genres = item.get("subGenres") or []
                for sg in sub_genres:
                    tags.append(sg)
                    
                # Unique list of tags
                tags = list(set(tags))
                
                # Determine cover URLs
                cover_v = item.get("posterVt")
                cover_h = item.get("posterHz")
                cover_url = cover_h or cover_v
                
                # Episode info text
                episode_info = ""
                ep_all = item.get("episodeAll")
                ep_updated = item.get("episodeUpdated")
                if ep_all and ep_updated:
                    if ep_all == ep_updated:
                        episode_info = f"Lengkap ({ep_all} EP)"
                    else:
                        episode_info = f"Update ke EP {ep_updated}/{ep_all}"
                elif ep_updated:
                    episode_info = f"Update ke EP {ep_updated}"
                
                formatted_results.append({
                    "id": item.get("cid"),
                    "cid": item.get("cid"),
                    "title": item.get("title"),
                    "subtitle": item.get("secondTitle"),
                    "description": item.get("description"),
                    "cover": cover_url,
                    "cover_v": cover_v,
                    "cover_h": cover_h,
                    "episode_info": episode_info,
                    "tags": tags,
                    "is_vip": is_vip,
                    "score": item.get("score") or "0"
                })
                
            return {
                "status": "success",
                "query": query,
                "page_no": page_no,
                "total_results": search_data.get("count", 0),
                "data": formatted_results
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Kesalahan koneksi ke WeTV API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kesalahan server internal: {str(e)}")
