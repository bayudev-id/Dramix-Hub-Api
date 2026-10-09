from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
import httpx
import logging
import os

router = APIRouter()
logger = logging.getLogger("viu-proxy.home")

VIU_API_GATEWAY = "https://api-gateway-global.viu.com"

from token_manager import get_proxy_headers

@router.get("/api/audienceTargeting/recommendations")
async def get_recommendations(request: Request):
    """
    Proxies recommendations / carousels (home grids) in real-time.
    """
    query_params = dict(request.query_params)
    
    # Viu API is messy and requires both snake_case and camelCase parameters
    if "areaId" not in query_params:
        query_params["areaId"] = query_params.get("area_id", "1000")
    if "languageId" not in query_params:
        query_params["languageId"] = query_params.get("language_flag_id", "8")
    if "platform" not in query_params:
        query_params["platform"] = query_params.get("platform_flag_label", "web")
    if "countryCode" not in query_params:
        query_params["countryCode"] = "ID"
    if "deviceId" not in query_params:
        query_params["deviceId"] = "00000000-0000-0000-0000-000000000000"
        
    logger.info(f"Proxying /api/audienceTargeting/recommendations with params: {query_params}")
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/audienceTargeting/recommendations",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={"Content-Type": resp.headers.get("content-type", "application/json")}
        )
    except Exception as e:
        logger.error(f"Error proxying recommendations: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )

@router.get("/api/user/info")
async def get_user_info(request: Request):
    """
    Proxies active user session and settings profile in real-time.
    """
    query_params = dict(request.query_params)
    logger.info(f"Proxying /api/user/info with params: {query_params}")
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/user/info",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={"Content-Type": resp.headers.get("content-type", "application/json")}
        )
    except Exception as e:
        logger.error(f"Error proxying user/info: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )

@router.get("/api/subscription/status")
async def get_subscription_status(request: Request):
    """
    Proxies active user plan and subscription permissions in real-time.
    """
    query_params = dict(request.query_params)
    logger.info(f"Proxying /api/subscription/status with params: {query_params}")
    headers = get_proxy_headers(request)
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/subscription/status",
            params=query_params,
            headers=headers,
            timeout=10.0
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={"Content-Type": resp.headers.get("content-type", "application/json")}
        )
    except Exception as e:
        logger.error(f"Error proxying subscription/status: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )
