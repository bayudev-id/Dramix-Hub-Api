"""FastAPI router for authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from src.client.iqiyi_client import IQIYIClient, LoginError
from src.models.schemas import StandardResponse, LoginRequest, AuthStatusData

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Dependency provider for IQIYIClient singleton
_client_instance: Optional[IQIYIClient] = None


def get_client() -> IQIYIClient:
    """Dependency provider returning singleton IQIYIClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = IQIYIClient()
    return _client_instance


def set_client(client: IQIYIClient) -> None:
    """Set custom client instance (for testing)."""
    global _client_instance
    _client_instance = client


@router.post("/login", response_model=StandardResponse[AuthStatusData])
def login(payload: LoginRequest, client: IQIYIClient = Depends(get_client)):
    """
    Authenticate against iQIYI Passport with phone/username and password.
    
    Persists active session to local JSON file upon success.
    """
    try:
        session = client.login(payload.username, payload.password)
        data = AuthStatusData(
            is_active=session.get("is_active", True),
            vip_status=session.get("vip_status", False),
            account_identifier=session.get("account_identifier"),
            vip_type=session.get("vip_type"),
            created_at=session.get("created_at"),
        )
        return StandardResponse[AuthStatusData](
            code=status.HTTP_200_OK,
            message="Login successful",
            data=data,
        )
    except LoginError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": str(e), "data": None},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Server error: {e}", "data": None},
        )


@router.get("/status", response_model=StandardResponse[AuthStatusData])
def get_status(client: IQIYIClient = Depends(get_client)):
    """
    Retrieve active iQIYI authentication session status with automatic live VIP check.
    """
    session = client.get_active_session()
    if not session or not session.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "No active session found", "data": None},
        )

    # Perform automatic live check against upstream iQIYI
    live_vip = None
    live_type = None
    try:
        live_status = client.check_vip_status()
        if isinstance(live_status, dict):
            live_vip = live_status.get("vip_status")
            live_type = live_status.get("vip_type")
    except Exception:
        pass

    vip_status = live_vip if isinstance(live_vip, bool) else session.get("vip_status", False)
    vip_type = live_type if isinstance(live_type, str) else session.get("vip_type")

    data = AuthStatusData(
        is_active=True,
        vip_status=vip_status,
        account_identifier=session.get("account_identifier"),
        vip_type=vip_type,
        created_at=session.get("created_at"),
    )
    return StandardResponse[AuthStatusData](
        code=status.HTTP_200_OK,
        message="Active session found",
        data=data,
    )
