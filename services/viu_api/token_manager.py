import os
import json
import logging
import httpx
import random
import uuid
from fastapi import Request

logger = logging.getLogger("viu-proxy.token_manager")

TOKEN_FILE = "viu_session.json"
VIU_API_GATEWAY = "https://api-gateway-global.viu.com"

# Memory cache for active token
_cached_token = None

def generate_guest_token() -> str:
    """
    Generates a brand new guest token from the Viu API Gateway synchronously.
    """
    logger.info("Generating a brand new guest token from Viu API Gateway...")
    rand = ''.join(random.choices('0123456789', k=10))
    url = f'{VIU_API_GATEWAY}/api/auth/token?v={rand}000'
    payload = {
        'countryCode': 'ID',
        'platform': 'browser',
        'platformFlagLabel': 'web',
        'language': 'id',
        'uuid': str(uuid.uuid4()),
        'carrierId': '0',
    }
    
    # Clean up NO_PROXY to prevent httpx crashes
    no_proxy = os.environ.get("NO_PROXY", "")
    if no_proxy:
        parts = [p.strip() for p in no_proxy.split(",")]
        cleaned_parts = [p for p in parts if not (":" in p and not (p.startswith("[") and "]" in p))]
        os.environ["NO_PROXY"] = ",".join(cleaned_parts)

    try:
        guest_headers = {
            'Content-Type': 'application/json',
            'X-Forwarded-For': '114.122.0.1',
            'X-Real-IP': '114.122.0.1'
        }
        with httpx.Client() as client:
            resp = client.post(url, json=payload, headers=guest_headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token")
                if token:
                    save_token(token)
                    logger.info("Successfully generated and saved new guest token.")
                    return token
            logger.error(f"Failed to generate guest token. Status: {resp.status_code}, Body: {resp.text}")
    except Exception as e:
        logger.error(f"Exception during guest token generation: {e}")
    return ""

def load_token() -> str:
    """
    Loads token from viu_session.json, generates a fresh guest token if missing, or falls back to .env
    """
    global _cached_token
    if _cached_token:
        return _cached_token

    # 1. Try reading from JSON session file
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                token = data.get("token")
                if token:
                    _cached_token = token
                    logger.info("Loaded Viu token from viu_session.json cache.")
                    return token
        except Exception as e:
            logger.error(f"Error reading viu_session.json: {e}")

    # 2. Automatically generate fresh guest token if cache is empty
    logger.info("No cached token found in viu_session.json. Fetching new guest token...")
    token = generate_guest_token()
    if token:
        return token


    # 2. Fall back to .env
    token = os.getenv("VIU_FALLBACK_TOKEN")
    if token:
        _cached_token = token
        logger.info("Loaded Viu token from .env fallback.")
        return token

    logger.warning("No Viu token found in viu_session.json or .env!")
    return ""

def save_token(token: str):
    """
    Saves new token to memory cache and viu_session.json
    """
    global _cached_token
    _cached_token = token
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": token}, f, indent=2)
        logger.info("Successfully updated and persisted new Viu token.")
    except Exception as e:
        logger.error(f"Failed to persist Viu token to JSON file: {e}")

async def verify_token_health(token: str, http_client: httpx.AsyncClient) -> bool:
    """
    Verifies if a token is valid by making a test request to user/info
    """
    details = await get_token_details(token, http_client)
    return details.get("is_healthy", False)

async def get_token_details(token: str, http_client: httpx.AsyncClient) -> dict:
    """
    Fetches user info and subscription details to determine token health and level (Free/VIP).
    """
    if not token:
        return {"is_healthy": False, "user_level": 0, "payment_status": "none", "plan_name": "None"}
    try:
        # 1. Fetch user info
        resp = await http_client.get(
            f"{VIU_API_GATEWAY}/api/user/info",
            params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": "https://www.viu.com",
                "Referer": "https://www.viu.com/",
                "Platform": "Web",
                "platformFlagLabel": "web",
                "X-Forwarded-For": "114.122.0.1",
                "X-Real-IP": "114.122.0.1"
            },
            timeout=5.0
        )
        if resp.status_code != 200:
            return {"is_healthy": False, "user_level": 0, "payment_status": "none", "plan_name": "None"}
        
        data = resp.json()
        if data.get("status", {}).get("code") != 0:
            return {"is_healthy": False, "user_level": 0, "payment_status": "none", "plan_name": "None"}
            
        user_data = data.get("data", {})
        user_level = user_data.get("user_level", 0)
        plan_name = user_data.get("user", {}).get("privileges", {}).get("planName", "Free")
        
        # 2. Fetch subscription status
        payment_status = "free"
        try:
            sub_resp = await http_client.get(
                f"{VIU_API_GATEWAY}/api/subscription/status",
                params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Origin": "https://www.viu.com",
                    "Referer": "https://www.viu.com/",
                    "Platform": "Web",
                    "platformFlagLabel": "web",
                    "X-Forwarded-For": "114.122.0.1",
                    "X-Real-IP": "114.122.0.1"
                },
                timeout=5.0
            )
            if sub_resp.status_code == 200:
                sub_data = sub_resp.json()
                payment_status = sub_data.get("paymentStatus", "free")
        except Exception as sub_err:
            logger.error(f"Failed to fetch subscription status for token details: {sub_err}")

        is_vip = user_level > 0 or payment_status in ["paid", "subscribed"] or (plan_name not in ["Free", "Basic_ID", "Basic"])
        return {
            "is_healthy": True,
            "user_level": user_level,
            "payment_status": payment_status,
            "plan_name": plan_name,
            "is_vip": is_vip
        }
    except Exception as e:
        logger.error(f"Error checking token details: {e}")
        return {"is_healthy": False, "user_level": 0, "payment_status": "none", "plan_name": "None"}

def extract_token_from_header(auth_header: str) -> str:
    """
    Helper to extract bearer token string from Authorization header
    """
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return auth_header or ""

def get_proxy_headers(request: Request) -> dict:
    """
    Unified request header builder with token auto-learning and injection.
    """
    headers = {}
    keys_to_discard = {
        "host", "accept-encoding", "origin", "referer", "authorization",
        "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site", "sec-fetch-user"
    }
    for k, v in request.headers.items():
        if k.lower() not in keys_to_discard:
            headers[k] = v

    # Strip any incoming IP-forwarding/geo headers to prevent Singapore/US IP leaks
    ip_keys_to_remove = [
        "x-forwarded-for", "x-real-ip", "cf-connecting-ip", "client-ip", 
        "x-client-ip", "forwarded", "x-vercel-ip-country", "x-vercel-forwarded-for"
    ]
    for key in list(headers.keys()):
        if key.lower() in ip_keys_to_remove:
            headers.pop(key)

    # Spoof Indonesian IP (Jakarta, Indonesia) to override any geolocation checks
    headers["X-Forwarded-For"] = "114.122.0.1"
    headers["X-Real-IP"] = "114.122.0.1"

    # Inject Origin and Referer for Viu CSRF protection
    headers["Origin"] = "https://www.viu.com"
    headers["Referer"] = "https://www.viu.com/"
    headers["Platform"] = "Web"
    headers["platformFlagLabel"] = "web"

    # Prioritize token from query params first (always overrides any incoming headers)
    query_token = request.query_params.get("token") or request.query_params.get("_token")
    
    # Case-insensitive header check for Authorization
    client_auth = None
    for k, v in request.headers.items():
        if k.lower() == "authorization":
            client_auth = v
            break

    # Clean the client_auth token if present
    clean_client_token = None
    if client_auth:
        token_str = extract_token_from_header(client_auth)
        if token_str and token_str.strip() not in ["", "undefined", "null"]:
            clean_client_token = token_str.strip()

    active_token = None
    api_secret = os.getenv("API_SECRET_KEY", "").strip()
    if query_token and query_token.strip() not in ["", "undefined", "null"]:
        active_token = query_token.strip()
        # Jangan pelajari API_SECRET_KEY sebagai token VIU (itu kunci proteksi kita, bukan token Viu)
        if active_token == api_secret:
            active_token = load_token()
            logger.info("Query token sama dengan API_SECRET_KEY, pakai cached Viu token.")
        else:
            logger.info("Using token from query parameters.")
    elif clean_client_token:
        # Abaikan Authorization Bearer yg isinya API_SECRET_KEY (dikirim frontend secureFetch)
        if api_secret and clean_client_token == api_secret:
            active_token = load_token()
            logger.info("Header token sama dengan API_SECRET_KEY, pakai cached Viu token.")
        else:
            active_token = clean_client_token
            # Auto-learn
            if clean_client_token != load_token():
                logger.info("Auto-Learn: Intercepted a new token in client request headers. Updating cache.")
                save_token(clean_client_token)
    else:
        active_token = load_token()

    if active_token:
        # Overwrite any existing casing of authorization header to avoid duplicates
        keys_to_remove = [k for k in headers.keys() if k.lower() == "authorization"]
        for k in keys_to_remove:
            headers.pop(k)
        headers["Authorization"] = f"Bearer {active_token}"

    return headers
