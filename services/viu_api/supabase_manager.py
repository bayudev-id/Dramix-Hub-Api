import os
import logging
import httpx
from datetime import datetime

logger = logging.getLogger("viu-proxy.supabase_manager")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Flag to verify if Supabase credentials are configured
SUPABASE_CONFIGURED = bool(SUPABASE_URL and SUPABASE_KEY)

if not SUPABASE_CONFIGURED:
    logger.warning("Supabase integration is NOT configured! Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")

def _get_headers() -> dict:
    """
    Returns standard headers required by Supabase REST API (PostgREST)
    """
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

async def save_session(
    user_id: int,
    username: str,
    nickname: str,
    token: str,
    access_token: str,
    is_vip: bool,
    plan_name: str,
    payment_status: str,
    device_list: list,
    last_login_time: str = None
) -> bool:
    """
    Saves or updates (upserts) a session to Supabase database.
    """
    if not SUPABASE_CONFIGURED:
        logger.warning("Supabase credentials not configured. Skipping save_session.")
        return False
        
    url = f"{SUPABASE_URL}/rest/v1/viu_sessions"
    headers = _get_headers()
    # Add Prefer headers for PostgREST Upsert behaviour
    headers["Prefer"] = "resolution=merge-duplicates"
    
    # If last_login_time is not provided, use current ISO time
    if not last_login_time:
        last_login_time = datetime.utcnow().isoformat() + "Z"
        
    payload = {
        "user_id": user_id,
        "username": username,
        "nickname": nickname,
        "token": token,
        "access_token": access_token,
        "is_vip": is_vip,
        "plan_name": plan_name,
        "payment_status": payment_status,
        "device_list": device_list,
        "last_login_time": last_login_time,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                params={"on_conflict": "user_id"},
                json=payload,
                headers=headers,
                timeout=10.0
            )
            if resp.status_code in [200, 201]:
                logger.info(f"Successfully upserted session for user {username} in Supabase.")
                return True
            else:
                logger.error(f"Failed to upsert session to Supabase. HTTP {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error connecting to Supabase in save_session: {e}")
        return False

async def get_active_vip_token() -> str:
    """
    Queries Supabase to retrieve the most recently updated active VIP token.
    Returns the token string, or None if no VIP session exists.
    """
    if not SUPABASE_CONFIGURED:
        return None
        
    url = f"{SUPABASE_URL}/rest/v1/viu_sessions"
    headers = _get_headers()
    params = {
        "is_vip": "eq.true",
        "order": "updated_at.desc",
        "limit": "1"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=5.0)
            if resp.status_code == 200:
                records = resp.json()
                if records and len(records) > 0:
                    vip_token = records[0].get("token")
                    logger.info(f"Loaded VIP token fallback from Supabase for user {records[0].get('username')}.")
                    return vip_token
            else:
                logger.error(f"Failed to query VIP session from Supabase. HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error querying Supabase in get_active_vip_token: {e}")
        
    return None

async def get_all_sessions() -> list:
    """
    Retrieves all sessions stored in the Supabase database.
    """
    if not SUPABASE_CONFIGURED:
        return []
        
    url = f"{SUPABASE_URL}/rest/v1/viu_sessions"
    headers = _get_headers()
    params = {
        "order": "updated_at.desc"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Failed to fetch sessions from Supabase. HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error connecting to Supabase in get_all_sessions: {e}")
        
    return []

async def delete_session(user_id: int) -> bool:
    """
    Removes a session from Supabase on logout.
    """
    if not SUPABASE_CONFIGURED:
        return False
        
    url = f"{SUPABASE_URL}/rest/v1/viu_sessions"
    headers = _get_headers()
    params = {
        "user_id": f"eq.{user_id}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, params=params, headers=headers, timeout=5.0)
            if resp.status_code in [200, 204]:
                logger.info(f"Successfully deleted session for user_id {user_id} in Supabase.")
                return True
            else:
                logger.error(f"Failed to delete session from Supabase. HTTP {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error connecting to Supabase in delete_session: {e}")
        return False
