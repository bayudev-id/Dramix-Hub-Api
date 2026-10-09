from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
import httpx
import logging

router = APIRouter()
logger = logging.getLogger("viu-proxy.config")

VIU_API_GATEWAY = "https://api-gateway-global.viu.com"

@router.get("/api/config")
async def get_config(request: Request):
    """
    Proxies Viu Configuration endpoint in real-time.
    """
    query_params = dict(request.query_params)
    logger.info(f"Proxying /api/config with params: {query_params}")
    
    # Clean and forward headers
    headers = {}
    for k, v in request.headers.items():
        if k.lower() not in ["host", "accept-encoding"]:
            headers[k] = v
            
    headers["Origin"] = "https://www.viu.com"
    headers["Referer"] = "https://www.viu.com/"
    
    client: httpx.AsyncClient = request.app.state.http_client
    
    try:
        resp = await client.get(
            f"{VIU_API_GATEWAY}/api/config",
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
        logger.error(f"Error proxying config: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 0, "error": {"message": f"Proxy error: {str(e)}"}}
        )
