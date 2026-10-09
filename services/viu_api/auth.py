from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import httpx
import logging
from typing import Optional

from token_manager import load_token, save_token, get_token_details
import supabase_manager

router = APIRouter()
logger = logging.getLogger("viu-proxy.auth")

VIU_API_GATEWAY = "https://api-gateway-global.viu.com"

class LoginRequest(BaseModel):
    phone: str
    password: str
    provider: Optional[str] = "phone"

class ActivateSessionRequest(BaseModel):
    user_id: int
    token: str

@router.post("/api/auth/login")
async def login_user(request: Request, body: LoginRequest):
    """
    Log in using Viu credentials, gather full user metadata and active device list,
    save the session to Supabase and update local active proxy token.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    
    # 1. Authenticate with Viu
    login_payload = {
        "phone": body.phone,
        "password": body.password,
        "provider": body.provider
    }
    
    # Viu requires a Bearer token (even an anonymous/guest one) in the Authorization header for login
    existing_token = load_token()
    if not existing_token:
        from token_manager import generate_guest_token
        existing_token = generate_guest_token()
        
    logger.info(f"Attempting Viu login for phone: {body.phone}")
    headers = {
        "Authorization": f"Bearer {existing_token}" if existing_token else "",
        "Origin": "https://umc-global.viu.com",
        "Referer": "https://umc-global.viu.com/",
        "Platform": "Web",
        "platformFlagLabel": "web",
        "Content-Type": "application/json"
    }
    
    try:
        viu_resp = await client.post(
            f"{VIU_API_GATEWAY}/api/auth/login",
            json=login_payload,
            headers=headers,
            timeout=10.0
        )
    except Exception as e:
        logger.error(f"Error during Viu login POST request: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi server Viu: {str(e)}")
        
    # Check if the token was expired/invalid, required, or has active session
    is_token_error = False
    if viu_resp.status_code in [400, 401]:
        is_token_error = True
    else:
        try:
            resp_data = viu_resp.json()
            if resp_data.get("status") == 0 and "error" in resp_data:
                err_code = str(resp_data["error"].get("code", "")).lower()
                err_msg = str(resp_data["error"].get("message", "")).lower()
                if ("jwt" in err_code or "token" in err_code or 
                    "token is required" in err_msg or 
                    "already logged in" in err_code or 
                    "already logged in" in err_msg):
                    is_token_error = True
        except:
            pass

    if is_token_error:
        logger.warning("Viu authentication server rejected the token or token is required. Fetching a fresh guest token and retrying login...")
        from token_manager import generate_guest_token
        new_token = generate_guest_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            try:
                viu_resp = await client.post(
                    f"{VIU_API_GATEWAY}/api/auth/login",
                    json=login_payload,
                    headers=headers,
                    timeout=10.0
                )
            except Exception as e:
                logger.error(f"Error during Viu login retry POST request: {e}")
                raise HTTPException(status_code=500, detail=f"Gagal menghubungi server Viu saat mencoba ulang: {str(e)}")
        else:
            logger.error("Failed to generate a fresh guest token for retry.")

    if viu_resp.status_code != 200:
        raise HTTPException(
            status_code=viu_resp.status_code, 
            detail=f"Error autentikasi server Viu: {viu_resp.text}"
        )
        
    viu_data = viu_resp.json()
    if viu_data.get("status") != 1:
        error_msg = viu_data.get("message", "Username atau password salah.")
        raise HTTPException(status_code=400, detail=error_msg)
        
    user_info = viu_data.get("user", {})
    user_id = user_info.get("userId")
    token = viu_data.get("token")
    access_token = viu_data.get("mc", {}).get("accessToken", "")
    username = user_info.get("username", body.phone)
    nickname = user_info.get("nickname", username)
    
    if not token:
        raise HTTPException(status_code=500, detail="Token tidak ditemukan dalam respon Viu.")
        
    logger.info(f"Viu login successful. User ID: {user_id}. Fetching additional account details...")
    
    # 2. Fetch User Profile Info & Subscription status using the token
    details = await get_token_details(token, client)
    is_vip = details.get("is_vip", False)
    plan_name = details.get("plan_name", "Free")
    payment_status = details.get("payment_status", "free")
    
    # 3. Fetch list of currently logged-in devices
    device_list = []
    try:
        dev_resp = await client.get(
            f"{VIU_API_GATEWAY}/api/concurrency/deviceList",
            params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": "https://www.viu.com",
                "Referer": "https://www.viu.com/",
                "Platform": "Web",
                "platformFlagLabel": "web"
            },
            timeout=5.0
        )
        if dev_resp.status_code == 200:
            dev_data = dev_resp.json()
            device_list = dev_data.get("deviceList", [])
    except Exception as dev_err:
        logger.error(f"Failed to fetch Viu deviceList: {dev_err}")
        
    # 4. Save session into Supabase
    supabase_saved = await supabase_manager.save_session(
        user_id=user_id,
        username=username,
        nickname=nickname,
        token=token,
        access_token=access_token,
        is_vip=is_vip,
        plan_name=plan_name,
        payment_status=payment_status,
        device_list=device_list,
        last_login_time=user_info.get("lastLoginTime")
    )
    
    # 5. Save locally in local proxy session json and memory cache
    save_token(token)
    
    return {
        "status": "success",
        "message": "Login berhasil dan disinkronkan ke Supabase.",
        "user_id": user_id,
        "username": username,
        "nickname": nickname,
        "is_vip": is_vip,
        "plan_name": plan_name,
        "payment_status": payment_status,
        "device_list": device_list,
        "token": token,
        "supabase_synced": supabase_saved
    }

@router.post("/api/auth/logout")
async def logout_user(request: Request):
    """
    Log out from Viu, remove the session from Supabase, and reset the active token cache.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    active_token = load_token()
    
    if not active_token:
        return {"status": "success", "message": "Tidak ada sesi aktif untuk keluar."}
        
    # Get user_id first to clean from Supabase
    user_id = None
    try:
        profile_resp = await client.get(
            f"{VIU_API_GATEWAY}/api/user/info",
            params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
            headers={
                "Authorization": f"Bearer {active_token}",
                "Origin": "https://www.viu.com",
                "Referer": "https://www.viu.com/",
                "Platform": "Web",
                "platformFlagLabel": "web"
            },
            timeout=5.0
        )
        if profile_resp.status_code == 200:
            profile_data = profile_resp.json()
            user_id = profile_data.get("data", {}).get("user_id")
    except Exception as e:
        logger.error(f"Could not fetch user ID during logout process: {e}")
        
    # Perform logout request to Viu API
    try:
        await client.post(
            f"{VIU_API_GATEWAY}/api/auth/logout",
            params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
            headers={
                "Authorization": f"Bearer {active_token}",
                "Origin": "https://www.viu.com",
                "Referer": "https://www.viu.com/",
                "Platform": "Web",
                "platformFlagLabel": "web"
            },
            timeout=5.0
        )
        logger.info("Successfully requested logout from Viu API.")
    except Exception as e:
        logger.error(f"Error during Viu logout request: {e}")
        
    # Delete from Supabase if we resolved user_id
    supabase_deleted = False
    if user_id:
        supabase_deleted = await supabase_manager.delete_session(user_id)
        
    # Reset local active token to empty (will cause fallback to VIU_FALLBACK_TOKEN)
    save_token("")
    
    return {
        "status": "success",
        "message": "Logout berhasil dilakukan.",
        "supabase_cleaned": supabase_deleted
    }

@router.get("/api/auth/profile")
async def get_profile(request: Request):
    """
    Get detailed account and device concurrency info for the current active token.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    active_token = load_token()
    
    if not active_token:
        return {"is_logged_in": False, "message": "Belum ada token aktif."}
        
    try:
        # 1. Fetch profile details
        prof_resp = await client.get(
            f"{VIU_API_GATEWAY}/api/user/info",
            params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
            headers={
                "Authorization": f"Bearer {active_token}",
                "Origin": "https://www.viu.com",
                "Referer": "https://www.viu.com/",
                "Platform": "Web",
                "platformFlagLabel": "web"
            },
            timeout=5.0
        )
        if prof_resp.status_code != 200:
            return {"is_logged_in": False, "message": "Sesi kedaluwarsa atau token tidak valid."}
            
        prof_data = prof_resp.json()
        if prof_data.get("status", {}).get("code") != 0:
            return {"is_logged_in": False, "message": "Token tidak valid menurut API Viu."}
            
        user_info = prof_data.get("data", {})
        
        # 2. Fetch subscription status
        payment_status = "free"
        try:
            sub_resp = await client.get(
                f"{VIU_API_GATEWAY}/api/subscription/status",
                params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
                headers={
                    "Authorization": f"Bearer {active_token}",
                    "Origin": "https://www.viu.com",
                    "Referer": "https://www.viu.com/",
                    "Platform": "Web",
                    "platformFlagLabel": "web"
                },
                timeout=5.0
            )
            if sub_resp.status_code == 200:
                payment_status = sub_resp.json().get("paymentStatus", "free")
        except Exception:
            pass
            
        # 3. Fetch device concurrency list
        device_list = []
        try:
            dev_resp = await client.get(
                f"{VIU_API_GATEWAY}/api/concurrency/deviceList",
                params={"platform_flag_label": "web", "area_id": "1000", "language_flag_id": "8"},
                headers={
                    "Authorization": f"Bearer {active_token}",
                    "Origin": "https://www.viu.com",
                    "Referer": "https://www.viu.com/",
                    "Platform": "Web",
                    "platformFlagLabel": "web"
                },
                timeout=5.0
            )
            if dev_resp.status_code == 200:
                device_list = dev_resp.json().get("deviceList", [])
        except Exception:
            pass
            
        user_level = user_info.get("user_level", 0)
        plan_name = user_info.get("user", {}).get("privileges", {}).get("planName", "Free")
        is_vip = user_level > 0 or payment_status in ["paid", "subscribed"] or plan_name not in ["Free", "Basic_ID", "Basic"]
        
        # Proactively update Supabase data with the newest details in case device lists or payment status changed
        user_id = user_info.get("user_id")
        if user_id:
            await supabase_manager.save_session(
                user_id=user_id,
                username=user_info.get("username", "user"),
                nickname=user_info.get("nickname", "user"),
                token=active_token,
                access_token="",
                is_vip=is_vip,
                plan_name=plan_name,
                payment_status=payment_status,
                device_list=device_list,
                last_login_time=user_info.get("user", {}).get("last_login_time")
            )
        
        return {
            "is_logged_in": True,
            "user_id": user_id,
            "username": user_info.get("username"),
            "nickname": user_info.get("nickname"),
            "is_vip": is_vip,
            "plan_name": plan_name,
            "payment_status": payment_status,
            "device_list": device_list
        }
    except Exception as e:
        logger.error(f"Error fetching active session profile: {e}")
        return {"is_logged_in": False, "message": f"Eror pemrosesan profil: {str(e)}"}

@router.get("/api/supabase/sessions")
async def get_supabase_sessions():
    """
    Get all active sessions currently saved in the Supabase database.
    """
    sessions = await supabase_manager.get_all_sessions()
    return {
        "status": "success",
        "count": len(sessions),
        "sessions": sessions
    }

@router.post("/api/supabase/sessions/activate")
async def activate_supabase_session(body: ActivateSessionRequest):
    """
    Manually switch the active local token of the proxy server to one of the tokens saved in Supabase.
    """
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token tidak boleh kosong.")
        
    save_token(token)
    logger.info(f"Activated Supabase session token locally for user_id {body.user_id}.")
    return {
        "status": "success",
        "message": f"Sesi user {body.user_id} berhasil diaktifkan secara lokal."
    }
