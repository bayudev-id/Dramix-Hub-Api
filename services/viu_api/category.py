from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
import httpx
import logging
import os

router = APIRouter()
logger = logging.getLogger("viu-proxy.category")

VIU_API_GATEWAY = "https://api-gateway-global.viu.com"

from token_manager import get_proxy_headers

@router.get("/api/mobile")
async def get_mobile_api(request: Request):
    """
    Proxies various category, grid, and catalog queries (via parameter r) in real-time.
    Examples:
      - /api/mobile?r=/category/series&category_id=549&length=44&offset=0
      - /api/mobile?r=/grid/index&grid_id=296656&length=44&offset=0
    """
    query_params = dict(request.query_params)
    
    # Process frontend page parameter (convert page=1,2,3 into offset=0,20,40)
    page_num = 1
    if "page" in query_params:
        try:
            page_num = int(query_params["page"])
            if page_num < 1:
                page_num = 1
        except ValueError:
            page_num = 1
        query_params.pop("page", None) # Remove 'page' before forwarding to Viu
        
        # Auto-calculate offset based on page: (page - 1) * 20
        query_params["offset"] = str((page_num - 1) * 20)
    
    # Force pagination length to exactly 20 dramas per page (multiples of 20)
    query_params["length"] = "20"
    
    # Auto-inject messy Viu parameters if missing (both snake_case and camelCase)
    if "area_id" not in query_params:
        query_params["area_id"] = "1000"
    if "language_flag_id" not in query_params:
        query_params["language_flag_id"] = "8"
    if "platform_flag_label" not in query_params:
        query_params["platform_flag_label"] = "web"

    if "areaId" not in query_params:
        query_params["areaId"] = query_params["area_id"]
    if "languageId" not in query_params:
        query_params["languageId"] = query_params["language_flag_id"]
    if "platform" not in query_params:
        query_params["platform"] = query_params["platform_flag_label"]
    if "platformFlagLabel" not in query_params:
        query_params["platformFlagLabel"] = query_params["platform_flag_label"]
    if "languageFlagId" not in query_params:
        query_params["languageFlagId"] = query_params["language_flag_id"]
    if "countryCode" not in query_params:
        query_params["countryCode"] = "ID"
    if "deviceId" not in query_params:
        query_params["deviceId"] = "00000000-0000-0000-0000-000000000000"
    if "ut" not in query_params:
        query_params["ut"] = "0"
        
    logger.info(f"Proxying /api/mobile with params: {query_params}")
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/mobile",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        
        # Intercept and enrich JSON with pagination details for infinity scroll
        try:
            resp_json = resp.json()
            if isinstance(resp_json, dict) and "data" in resp_json:
                data_block = resp_json["data"]
                if isinstance(data_block, dict) and "category_series_total" in data_block:
                    totals = data_block["category_series_total"]
                    if isinstance(totals, list) and len(totals) > 0:
                        total_str = totals[0].get("series_total", "0")
                        try:
                            series_total = int(total_str)
                            offset = int(query_params.get("offset", 0))
                            length = int(query_params.get("length", 20))
                            has_more = (offset + length) < series_total
                            
                            # Inject pagination flags into both the data block and root level for maximum frontend support
                            data_block["has_more"] = has_more
                            data_block["hasmore"] = has_more
                            data_block["ismore"] = has_more
                            data_block["page"] = page_num
                            data_block["next_page"] = page_num + 1 if has_more else None
                            
                            resp_json["has_more"] = has_more
                            resp_json["hasmore"] = has_more
                            resp_json["ismore"] = has_more
                            resp_json["page"] = page_num
                            resp_json["next_page"] = page_num + 1 if has_more else None
                        except ValueError:
                            pass
            return JSONResponse(content=resp_json, status_code=resp.status_code)
        except Exception:
            # Fallback to returning raw response if parsing fails or not JSON
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={"Content-Type": resp.headers.get("content-type", "application/json")}
            )
            
    except Exception as e:
        logger.error(f"Error proxying mobile API: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )

@router.get("/api/category")
async def get_category_list(request: Request):
    """
    Returns the mapped 14 categories in the specified format, localized dynamically.
    """
    query_params = dict(request.query_params)
    
    # Detect language (support lang, languageId, language_flag_id)
    lang = query_params.get("language_flag_id", query_params.get("languageId", query_params.get("lang", "8")))
    
    is_english = str(lang) == "3" or str(lang).lower().startswith("en")
    
    # Mapped 14 categories
    categories = [
        {"title_id": "Trailers", "title_en": "Trailers", "opId": "579", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Viu Original", "title_en": "Viu Original", "opId": "571", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Korea", "title_en": "Korean Drama", "opId": "549", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Variety Show Korea", "title_en": "Korean Variety Show", "opId": "550", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Cina", "title_en": "Chinese Drama", "opId": "553", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Thailand", "title_en": "Thai Drama", "opId": "552", "type": "SUBJECTS_MOVIE"},
        {"title_id": "TrueVisions NOW", "title_en": "TrueVisions NOW", "opId": "1092", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Dub Bahasa Indonesia", "title_en": "Indonesian Dubbed", "opId": "546", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Film Korea", "title_en": "Korean Movie", "opId": "551", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Film", "title_en": "Movie", "opId": "308", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Anime", "title_en": "Anime", "opId": "574", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Indonesia", "title_en": "Indonesian Drama", "opId": "548", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Turki", "title_en": "Turkish Drama", "opId": "557", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Variety Show", "title_en": "Variety Show", "opId": "573", "type": "SUBJECTS_MOVIE"},
        {"title_id": "Drama Korea Romantis", "title_en": "Romantic Korean Drama", "opId": "775", "type": "SUBJECTS_MOVIE"}
    ]
    
    from datetime import datetime, timezone
    data = []
    for cat in categories:
        data.append({
            "title": cat["title_en"] if is_english else cat["title_id"],
            "type": cat["type"],
            "category_id": cat["opId"]  # Changed opId to category_id
        })
        
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    return {
        "code": 200,
        "message": "Success",
        "provider": "viu",
        "timestamp": current_time,
        "data": data
    }
