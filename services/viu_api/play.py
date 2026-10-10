from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
import httpx
import logging
import os
import json

router = APIRouter()
logger = logging.getLogger("viu-proxy.play")

VIU_API_GATEWAY = "https://api-gateway-global.viu.com"
VIU_PROD_IN = "https://prod-in.viu.com"

from token_manager import get_proxy_headers
import supabase_manager
import re

def rewrite_m3u8_line(line: str, local_host: str, token: str, api_key: str = "") -> str:
    line = line.strip()
    if not line:
        return ""
        
    if line.startswith("#"):
        # It's a tag line. Look for URI="url" attributes
        def replace_uri(match):
            url = match.group(1)
            # Replace dms-api with local_host if present
            url = url.replace("https://dms-api.viu.com", local_host)
            if token and "token=" not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}token={token}"
            # ponytail: api_key moved to Authorization header via xhrSetup; re-add query auth only if player can't set headers
            return f'URI="{url}"'
            
        return re.sub(r'URI="([^"]+)"', replace_uri, line)
    else:
        # It's a plain URI line
        url = line
        url = url.replace("https://dms-api.viu.com", local_host)
        if token and "token=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}token={token}"
        return url

def rewrite_viu_urls(data, local_host, token, api_key: str = ""):
    if isinstance(data, dict):
        return {k: rewrite_viu_urls(v, local_host, token, api_key) for k, v in data.items()}
    elif isinstance(data, list):
        return [rewrite_viu_urls(item, local_host, token, api_key) for item in data]
    elif isinstance(data, str) and data.startswith("https://dms-api.viu.com"):
        rewritten = data.replace("https://dms-api.viu.com", local_host)
        if token:
            separator = "&" if "?" in rewritten else "?"
            rewritten = f"{rewritten}{separator}token={token}"
        return rewritten
    return data

@router.get("/api/playback/distribute")
async def get_playback_distribute(request: Request):
    """
    Proxies dynamic playback streaming feeds (HLS/Airplay playlists) in real-time.
    """
    query_params = dict(request.query_params)
    
    # Auto-inject messy Viu playback parameters if missing (both snake_case and camelCase)
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
        
    logger.info(f"Proxying /api/playback/distribute with params: {query_params}")
    # Buang kunci proteksi kita sebelum forward ke upstream (bukan param Viu)
    query_params.pop("api_key", None)
    query_params.pop("secret", None)
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/playback/distribute",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        
        # Intercept and attempt to extract full progressive TS download URL
        if resp.status_code == 200:
            try:
                resp_json = resp.json()
                
                is_preview = False
                # If paywall block is detected, attempt to recover using Supabase VIP token first
                if resp_json.get("status", {}).get("code") == 200003:
                    logger.info("Access Violated (200003) on full playback request. Attempting Supabase VIP fallback...")
                    vip_token = await supabase_manager.get_active_vip_token()
                    if vip_token:
                        logger.info("Found VIP token in Supabase. Retrying playback request with VIP credentials...")
                        vip_headers = headers.copy()
                        vip_headers["Authorization"] = f"Bearer {vip_token}"
                        try:
                            vip_resp = await client.get(
                                f"{VIU_API_GATEWAY}/api/playback/distribute",
                                params=query_params,
                                headers=vip_headers,
                                timeout=10.0
                            )
                            if vip_resp.status_code == 200:
                                vip_json = vip_resp.json()
                                if vip_json.get("status", {}).get("code") == 0:
                                    resp_json = vip_json
                                    headers = vip_headers  # Propagate VIP headers for downstream playlist requests
                                    logger.info("Supabase VIP bypass successful! Serving VIP full stream.")
                        except Exception as vip_err:
                            logger.error(f"Failed to fetch playback using Supabase VIP token: {vip_err}")
                
                # If still blocked (no VIP token or VIP token request failed), fall back to preview params
                if resp_json.get("status", {}).get("code") == 200003:
                    logger.info("Viu paywall active. Retrying with free preview parameters...")
                    preview_params = query_params.copy()
                    preview_params["duration"] = "180"
                    preview_params["duration_start"] = "0"
                    try:
                        preview_resp = await client.get(
                            f"{VIU_API_GATEWAY}/api/playback/distribute",
                            params=preview_params,
                            headers=headers,
                            timeout=10.0
                        )
                        if preview_resp.status_code == 200:
                            preview_json = preview_resp.json()
                            if preview_json.get("status", {}).get("code") == 0:
                                resp_json = preview_json
                                is_preview = True
                                logger.info("Auto-recovery successful! Serving preview stream.")
                    except Exception as preview_err:
                        logger.error(f"Failed to fetch preview fallback stream: {preview_err}")

                if resp_json.get("status", {}).get("code") == 0:
                    stream = resp_json.get("data", {}).get("stream", {})
                    m3u8_url = None
                    
                    # Search s1080p, s720p, s480p, s240p, or airplayurl in order of preference
                    for res_key in ["s1080p", "s720p", "s480p", "s240p", "airplayurl"]:
                        val = stream.get(res_key)
                        if isinstance(val, dict):
                            for sub_k, sub_val in val.items():
                                if isinstance(sub_val, str) and "m3u8" in sub_val:
                                    m3u8_url = sub_val
                                    break
                        elif isinstance(val, str) and "m3u8" in val:
                            m3u8_url = val
                        if m3u8_url:
                            break
                            
                    if m3u8_url:
                        # 1. Fetch master playlist
                        r_master = await client.get(m3u8_url, headers=headers, timeout=5.0)
                        media_url = None
                        for line in r_master.text.splitlines():
                            line = line.strip()
                            if line.startswith("http") and ("vuclip_vod" in line or "vod" in line or "m3u8" in line):
                                media_url = line
                                break
                                
                        if media_url:
                            # 2. Fetch media playlist
                            r_media = await client.get(media_url, headers=headers, timeout=5.0)
                            progressive_url = None
                            for line in r_media.text.splitlines():
                                line = line.strip()
                                if "output.ts?sign=" in line or ("http" in line and "output.ts" in line):
                                    progressive_url = line
                                    break
                                    
                            if progressive_url:
                                if not progressive_url.startswith("http"):
                                    from urllib.parse import urljoin
                                    progressive_url = urljoin(media_url, progressive_url)
                                    
                                # Resolve redirect to get the direct CDN URL (e.g. vuclip-bpcdn.viu.com)
                                # Only request if it's a dms-api.viu.com URL and use HEAD to prevent downloading the video file
                                if "dms-api.viu.com" in progressive_url:
                                    try:
                                        r_redirect = await client.head(progressive_url, headers=headers, follow_redirects=False, timeout=5.0)
                                        if r_redirect.status_code in [301, 302, 307, 308] and "Location" in r_redirect.headers:
                                            progressive_url = r_redirect.headers["Location"]
                                            logger.info(f"Resolved progressive URL redirect to direct CDN: {progressive_url[:120]}...")
                                    except Exception as redir_err:
                                        logger.error(f"Failed to resolve progressive URL redirect: {redir_err}")
                                    
                                resp_json["data"]["full_progressive_download_url"] = progressive_url
                                logger.info(f"Auto-extracted full progressive URL: {progressive_url[:120]}...")
                
                # Tag preview state in JSON for the frontend
                resp_json["is_preview"] = is_preview
                if is_preview:
                    resp_json["preview_duration"] = 180

                # Replace dms-api.viu.com with our local host and propagate token to proxy URLs
                scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                local_host = f"{scheme}://{request.headers.get('host', '127.0.0.1:6105')}"
                active_token = headers.get("Authorization", "").replace("Bearer ", "").strip()
                api_key = request.query_params.get("api_key") or request.query_params.get("secret") or os.getenv("API_SECRET_KEY", "").strip()
                resp_json = rewrite_viu_urls(resp_json, local_host, active_token, api_key)
                
                return JSONResponse(content=resp_json, status_code=200)
            except Exception as parse_err:
                logger.error(f"Failed to auto-extract progressive TS URL: {parse_err}")
                
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={"Content-Type": resp.headers.get("content-type", "application/json")}
        )
    except Exception as e:
        logger.error(f"Error proxying playback/distribute: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )

@router.get("/vod/vuclip_airplay.m3u8")
async def proxy_airplay_m3u8(request: Request):
    query_params = dict(request.query_params)
    # Extract DRM token and REMOVE it from query_params before forwarding upstream.
    drm_token = query_params.pop("token", None) or query_params.pop("_token", None)
    query_params.pop("api_key", None)
    query_params.pop("secret", None)
    # Now query_params has NO token, api_key, or secret — safe to forward
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    async def _fetch_airplay(hdrs: dict):
        return await client.get(
            "https://dms-api.viu.com/vod/vuclip_airplay.m3u8",
            params=query_params,
            headers=hdrs,
            timeout=10.0
        )
    
    try:
        resp = await _fetch_airplay(headers)
        
        # Auto-refresh token if upstream returns 401
        if resp.status_code == 401:
            logger.warning("[vuclip_airplay] Upstream 401 — token expired. Refreshing guest token and retrying...")
            from token_manager import generate_guest_token, save_token
            new_token = generate_guest_token()
            if new_token:
                save_token(new_token)
                headers["Authorization"] = f"Bearer {new_token}"
                resp = await _fetch_airplay(headers)
                logger.info(f"[vuclip_airplay] Retry after token refresh: status={resp.status_code}")
        
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        local_host = f"{scheme}://{request.headers.get('host', '127.0.0.1:6105')}"
        api_key = request.query_params.get("api_key") or request.query_params.get("secret") or os.getenv("API_SECRET_KEY", "").strip()
        
        content = resp.text.replace("https://prod-in.viu.com/api/appsdrm/getkey", f"{local_host}/api/appsdrm/getkey")
        
        lines = []
        for line in content.splitlines():
            lines.append(rewrite_m3u8_line(line, local_host, drm_token, api_key))
        content = "\n".join(lines)
        
        return Response(
            content=content,
            status_code=resp.status_code,
            headers={"Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error proxying airplay m3u8: {e}")
        return Response(status_code=500, content=f"Proxy error: {str(e)}")

@router.get("/vod/vuclip_vod.m3u8")
async def proxy_vod_m3u8(request: Request):
    query_params = dict(request.query_params)
    # Extract DRM token and REMOVE it from query_params before forwarding upstream.
    drm_token = query_params.pop("token", None) or query_params.pop("_token", None)
    query_params.pop("api_key", None)
    query_params.pop("secret", None)
    # Now query_params has NO token, api_key, or secret — safe to forward
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    async def _fetch_vod(hdrs: dict):
        return await client.get(
            "https://dms-api.viu.com/vod/vuclip_vod.m3u8",
            params=query_params,
            headers=hdrs,
            timeout=10.0
        )
    
    try:
        resp = await _fetch_vod(headers)
        
        # Auto-refresh token if upstream returns 401
        if resp.status_code == 401:
            logger.warning("[vuclip_vod] Upstream 401 — token expired. Refreshing guest token and retrying...")
            from token_manager import generate_guest_token, save_token
            new_token = generate_guest_token()
            if new_token:
                save_token(new_token)
                headers["Authorization"] = f"Bearer {new_token}"
                resp = await _fetch_vod(headers)
                logger.info(f"[vuclip_vod] Retry after token refresh: status={resp.status_code}")
        
        # Handle non-200 upstream responses with proper JSON body + explicit Content-Length
        if resp.status_code != 200:
            error_body = json.dumps({
                "error": "Access denied or upstream error",
                "status": resp.status_code,
                "message": resp.reason_phrase or f"HTTP {resp.status_code}"
            }).encode('utf-8')
            return Response(
                content=error_body,
                status_code=resp.status_code,
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Content-Length": str(len(error_body))
                }
            )
        
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        local_host = f"{scheme}://{request.headers.get('host', '127.0.0.1:6105')}"
        api_key = request.query_params.get("api_key") or request.query_params.get("secret") or os.getenv("API_SECRET_KEY", "").strip()
        
        content = resp.text.replace("https://prod-in.viu.com/api/appsdrm/getkey", f"{local_host}/api/appsdrm/getkey")
        
        lines = []
        for line in content.splitlines():
            lines.append(rewrite_m3u8_line(line, local_host, drm_token, api_key))
        content = "\n".join(lines)
        
        return Response(
            content=content,
            status_code=resp.status_code,
            headers={"Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error proxying vod m3u8: {e}")
        return Response(status_code=500, content=f"Proxy error: {str(e)}")

@router.get("/vod/{path:path}")
async def proxy_vod_fallback(path: str, request: Request):
    """
    Catch-all proxy for dynamic subtitle tracks, WebVTT files, and segments under /vod/.
    """
    query_params = dict(request.query_params)
    # Extract DRM token and REMOVE it from query_params before forwarding upstream.
    drm_token = query_params.pop("token", None) or query_params.pop("_token", None)
    query_params.pop("api_key", None)
    query_params.pop("secret", None)
    # Now query_params has NO token, api_key, or secret — safe to forward
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    url = f"https://dms-api.viu.com/vod/{path}"
    logger.info(f"Proxying fallback VOD path: {path} with params: {query_params}")
    try:
        resp = await client.get(
            url,
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        
        # Auto-refresh token if upstream returns 401
        if resp.status_code == 401:
            logger.warning(f"[vod_fallback] Upstream 401 for path={path} — token expired. Refreshing guest token and retrying...")
            from token_manager import generate_guest_token, save_token
            new_token = generate_guest_token()
            if new_token:
                save_token(new_token)
                headers["Authorization"] = f"Bearer {new_token}"
                resp = await client.get(url, params=query_params, headers=headers, timeout=10.0)
                logger.info(f"[vod_fallback] Retry after token refresh: status={resp.status_code}")
        
        content_type = resp.headers.get("content-type", "")
        # Rewrite URLs if response is an HLS playlist or subtitle file
        if (
            "mpegurl" in content_type or 
            "text" in content_type or 
            "application/x-mpegurl" in content_type or 
            path.endswith(".m3u8") or 
            path.endswith(".vtt")
        ):
            scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
            local_host = f"{scheme}://{request.headers.get('host', '127.0.0.1:6105')}"
            api_key = request.query_params.get("api_key") or request.query_params.get("secret") or os.getenv("API_SECRET_KEY", "").strip()
            try:
                content = resp.text.replace("https://prod-in.viu.com/api/appsdrm/getkey", f"{local_host}/api/appsdrm/getkey")
                
                lines = []
                for line in content.splitlines():
                    lines.append(rewrite_m3u8_line(line, local_host, drm_token, api_key))
                content = "\n".join(lines)
            except Exception as parse_err:
                logger.error(f"Error parsing fallback VOD content: {parse_err}")
                content = resp.content
            
            return Response(
                content=content,
                status_code=resp.status_code,
                headers={"Content-Type": content_type, "Access-Control-Allow-Origin": "*"}
            )
        else:
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={"Content-Type": content_type, "Access-Control-Allow-Origin": "*"}
            )
    except Exception as e:
        logger.error(f"Error proxying fallback VOD path {path}: {e}")
        return Response(status_code=500, content=f"Proxy error: {str(e)}")


@router.get("/api/appsdrm/getkey")
async def get_drm_key(request: Request):
    """
    Proxies DRM key resolution for protected streams in real-time.
    """
    query_params = dict(request.query_params)
    query_params.pop("token", None)
    query_params.pop("_token", None)
    query_params.pop("api_key", None)
    query_params.pop("secret", None)
    logger.info(f"Proxying /api/appsdrm/getkey with params: {query_params}")
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_PROD_IN}/api/appsdrm/getkey",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={"Content-Type": resp.headers.get("content-type", "application/octet-stream"), "Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error proxying appsdrm/getkey: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )

# ----------------------------------------------------------------------
# WeTV Style Unified Stream & Subtitle Endpoint
# ----------------------------------------------------------------------
@router.get("/drama-api/stream")
@router.get("/functions/v1/drama-api/stream")
@router.get("/api/drama-api/stream")
async def get_drama_stream_custom(
    request: Request,
    id: str = None,          # series_id
    episode_id: str = None,  # product_id / ccs_product_id
    provider: str = "viu"
):
    """
    Returns stream urls and subtitles in a standardized WeTV-like format.
    """
    from datetime import datetime
    import random
    import string

    # 1. Generate unique matching timestamp structure
    rand_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    timestamp = f"{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z [{rand_str}]"

    # Validation
    if not episode_id:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "Missing required parameter: episode_id",
                "provider": provider,
                "timestamp": timestamp,
                "data": None
            }
        )

    client: httpx.AsyncClient = request.app.state.http_client
    headers = get_proxy_headers(request)

    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    local_host = f"{scheme}://{request.headers.get('host', '127.0.0.1:6105')}"

    subtitles = []
    ccs_product_id = episode_id  # Fallback

    # Step A: Retrieve VOD Detail (Subtitles & Real ccs_product_id)
    try:
        detail_resp = await client.get(
            f"{VIU_API_GATEWAY}/api/mobile",
            params={
                "r": "/vod/detail",
                "product_id": episode_id,
                "platform_flag_label": "web",
                "area_id": "1000",
                "language_flag_id": "8",
                "os_flag_id": "1"
            },
            headers=headers,
            timeout=10.0
        )
        if detail_resp.status_code == 401:
            logger.warning(f"[get_drama_stream_custom] Upstream 401 on /vod/detail for {episode_id}. Refreshing guest token...")
            from token_manager import generate_guest_token
            new_token = generate_guest_token()
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                detail_resp = await client.get(
                    f"{VIU_API_GATEWAY}/api/mobile",
                    params={
                        "r": "/vod/detail",
                        "product_id": episode_id,
                        "platform_flag_label": "web",
                        "area_id": "1000",
                        "language_flag_id": "8",
                        "os_flag_id": "1"
                    },
                    headers=headers,
                    timeout=10.0
                )
        if detail_resp.status_code == 200:
            detail_json = detail_resp.json()
            current_product = detail_json.get("data", {}).get("current_product", {})
            if current_product:
                ccs_product_id = current_product.get("ccs_product_id") or episode_id
                raw_subs = current_product.get("subtitle", [])
                active_token = headers.get("Authorization", "").replace("Bearer ", "").strip()
                for sub in raw_subs:
                    lang_code = sub.get("code", "").upper()
                    sub_url = sub.get("subtitle_url") or sub.get("url")
                    if sub_url:
                        sub_url = sub_url.replace("https://dms-api.viu.com", local_host)
                        if active_token:
                            separator = "&" if "?" in sub_url else "?"
                            sub_url = f"{sub_url}{separator}token={active_token}"
                    subtitles.append({
                        "url": sub_url,
                        "lang": lang_code,
                        "label": sub.get("name")
                    })
    except Exception as e:
        logger.error(f"Error fetching VOD detail for {episode_id} in custom endpoint: {e}")

    # Step B: Retrieve HLS Stream distribution url list
    playback_params = {
        "ccs_product_id": ccs_product_id,
        "platform_flag_label": "web",
        "area_id": "1000",
        "language_flag_id": "8",
        "countryCode": "ID",
        "deviceId": "00000000-0000-0000-0000-000000000000",
        "ut": "0"
    }

    resp_json = None
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/playback/distribute",
            params=playback_params,
            headers=headers,
            timeout=10.0
        )
        if resp.status_code == 401:
            logger.warning("[get_drama_stream_custom] Upstream 401 on playback/distribute. Refreshing guest token and retrying...")
            from token_manager import generate_guest_token
            new_token = generate_guest_token()
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                resp = await client.get(
                    f"{VIU_API_GATEWAY}/api/playback/distribute",
                    params=playback_params,
                    headers=headers,
                    timeout=10.0
                )
                logger.info(f"[get_drama_stream_custom] Retry playback/distribute after token refresh: status={resp.status_code}")
        if resp.status_code == 200:
            resp_json = resp.json()

            # VIP bypass check
            if resp_json.get("status", {}).get("code") == 200003:
                logger.info("Access Violated (200003) on custom stream endpoint. Trying VIP fallback...")
                vip_token = await supabase_manager.get_active_vip_token()
                if vip_token:
                    vip_headers = headers.copy()
                    vip_headers["Authorization"] = f"Bearer {vip_token}"
                    try:
                        vip_resp = await client.get(
                            f"{VIU_API_GATEWAY}/api/playback/distribute",
                            params=playback_params,
                            headers=vip_headers,
                            timeout=10.0
                        )
                        if vip_resp.status_code == 200:
                            vip_json = vip_resp.json()
                            if vip_json.get("status", {}).get("code") == 0:
                                resp_json = vip_json
                                headers = vip_headers
                                logger.info("VIP bypass successful in custom stream endpoint.")
                    except Exception as vip_err:
                        logger.error(f"VIP fallback failed in custom stream: {vip_err}")

            # Preview fallback check if VIP bypass didn't resolve it or wasn't available
            if resp_json.get("status", {}).get("code") == 200003:
                logger.info("Access Violated (200003). Trying preview fallback in custom stream...")
                preview_params = playback_params.copy()
                preview_params["duration"] = "180"
                preview_params["duration_start"] = "0"
                try:
                    preview_resp = await client.get(
                        f"{VIU_API_GATEWAY}/api/playback/distribute",
                        params=preview_params,
                        headers=headers,
                        timeout=10.0
                    )
                    if preview_resp.status_code == 200:
                        preview_json = preview_resp.json()
                        if preview_json.get("status", {}).get("code") == 0:
                            resp_json = preview_json
                            logger.info("Preview fallback successful in custom stream endpoint.")
                except Exception as preview_err:
                    logger.error(f"Preview fallback failed in custom stream: {preview_err}")
    except Exception as e:
        logger.error(f"Error fetching playback details in custom endpoint: {e}")

    # Parse and structure streams
    streams = []
    if resp_json and resp_json.get("status", {}).get("code") == 0:
        stream_data = resp_json.get("data", {}).get("stream", {})

        # Loop through cdn options and airplay
        cdn_labels = {
            "url": "Byteplus",
            "url2": "Google",
            "airplayurl": "Airplay"
        }
        for source_key in ["url", "url2", "airplayurl"]:
            source_dict = stream_data.get(source_key) or {}
            for res_key, raw_url in source_dict.items():
                if raw_url:
                    base_quality = res_key.replace("s", "")
                    quality_label = f"{base_quality} ({cdn_labels[source_key]})"
                    proxied_url = raw_url.replace("https://dms-api.viu.com", local_host)
                    active_token = headers.get("Authorization", "").replace("Bearer ", "").strip()
                    if active_token:
                        separator = "&" if "?" in proxied_url else "?"
                        proxied_url = f"{proxied_url}{separator}token={active_token}"

                    # Eliminate duplicate URLs
                    if not any(s["quality"] == quality_label and s["url"] == proxied_url for s in streams):
                        streams.append({
                            "url": proxied_url,
                            "quality": quality_label,
                            "format": "hls"
                        })

    # Fallback to empty list or message if blocked
    message = "Success"
    code = 200
    if not streams:
        code = 403
        message = "Forbidden: Content might be VIP restricted and no active bypass worked."

    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "message": message,
            "provider": provider,
            "timestamp": timestamp,
            "data": {
                "streams": streams,
                "subtitles": subtitles,
                "dubs": []
            }
        }
    )


# ----------------------------------------------------------------------
# WeTV Style Unified Search Endpoint
# ----------------------------------------------------------------------
@router.get("/drama-api/search")
@router.get("/functions/v1/drama-api/search")
@router.get("/api/drama-api/search")
async def search_drama_custom(
    request: Request,
    query: str = None,
    keyword: str = None,
    q: str = None,
    page: int = 1,
    limit: int = 16,
    provider: str = "viu"
):
    """
    Unified WeTV style search endpoint proxying search queries directly to Viu's /search/video endpoint.
    """
    search_term = query or keyword or q
    if not search_term:
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "Missing search term parameter (query, keyword, or q)",
                "provider": provider,
                "data": []
            }
        )

    client: httpx.AsyncClient = request.app.state.http_client
    headers = get_proxy_headers(request)

    results = []
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/mobile",
            params={
                "r": "/search/video",
                "keyword": search_term,
                "page": str(page),
                "limit": str(limit),
                "platform_flag_label": "web",
                "area_id": "1000",
                "language_flag_id": "8"
            },
            headers=headers,
            timeout=10.0
        )
        
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json.get("status", {}).get("code") == 0:
                series_list = resp_json.get("data", {}).get("series") or []
                
                # Resolve product_id for each series via parallel product-list requests.
                # VIU search only returns series_id but the detail URL requires product_id
                # (first episode's product_id, which differs from series_id).
                async def resolve_product_id(s: dict) -> dict:
                    sid = s.get("series_id") or s.get("id")
                    try:
                        pl_resp = await client.get(
                            f"{VIU_API_GATEWAY}/api/mobile",
                            params={
                                "r": "/vod/product-list",
                                "series_id": str(sid),
                                "size": "1",
                                "sort": "ASC",
                                "platform_flag_label": "web",
                                "area_id": "1000",
                                "language_flag_id": "8"
                            },
                            headers=headers,
                            timeout=5.0
                        )
                        if pl_resp.status_code == 200:
                            pl_json = pl_resp.json()
                            products = pl_json.get("data", {}).get("product_list") or []
                            if products:
                                return {
                                    "id": str(products[0].get("product_id") or sid),
                                    "series_id": str(sid),
                                }
                    except Exception as resolve_err:
                        logger.warning(f"[search] Could not resolve product_id for series_id={sid}: {resolve_err}")
                    # Fallback to series_id if resolve fails
                    return {"id": str(sid), "series_id": str(sid)}

                import asyncio
                resolved = await asyncio.gather(*[resolve_product_id(s) for s in series_list])

                for s, r in zip(series_list, resolved):
                    results.append({
                        "id": r["id"],
                        "series_id": r["series_id"],
                        "title": s.get("name"),
                        "cover": s.get("cover_landscape_image_url") or s.get("cover_image_url") or s.get("series_image_url"),
                        "cover_portrait": s.get("cover_portrait_image_url"),
                        "category": s.get("category_name"),
                        "total_episodes": int(s.get("product_total") or 0) if s.get("product_total") else 0,
                        "latest_episode": int(s.get("released_product_total") or 0) if s.get("released_product_total") else 0,
                        "provider": "viu"
                    })
    except Exception as e:
        logger.error(f"Error executing custom search for '{search_term}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": f"Internal proxy search error: {str(e)}",
                "provider": provider,
                "data": []
            }
        )

    return JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "message": "Success",
            "provider": provider,
            "data": results
        }
    )


