"""FastAPI router for catalog endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from src.client.iqiyi_client import IQIYIClient
from src.models.schemas import (
    StandardResponse,
    DramaInfo,
    EpisodeInfo,
    SearchResult,
    FeedItem,
    TabInfo,
)
from production.api.routes_auth import get_client

router = APIRouter(prefix="/api", tags=["catalog"])


@router.post("/search", response_model=StandardResponse[SearchResult])
def search(
    keyword: str = Body(..., embed=True),
    pg_num: int = Body(1, embed=True),
    lang: str = Body("id_id", embed=True),
    client: IQIYIClient = Depends(get_client)
):
    """
    Search iQIYI catalog with pagination.
    
    Args:
        keyword: Search query term
        pg_num: Page number (default: 1)
        lang: Language preference (default: id_id)
    """
    if not keyword or keyword.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 400, "message": "keyword is required", "data": None}
        )
    
    try:
        result = client.search(keyword, pg_num, lang=lang)
        items = [DramaInfo(**item) for item in result.get("items", [])]
        search_result = SearchResult(
            keyword=result["keyword"],
            pg_num=result["pg_num"],
            has_more=result["has_more"],
            items=items,
        )
        return StandardResponse[SearchResult](
            code=200,
            message="success",
            data=search_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Search failed: {e}", "data": None}
        )


@router.get("/feed", response_model=StandardResponse[List[FeedItem]])
def get_feed(client: IQIYIClient = Depends(get_client)):
    """Fetch curated homepage feed items."""
    try:
        items_data = client.get_feed()
        items = [FeedItem(**item) for item in items_data]
        return StandardResponse[List[FeedItem]](
            code=200,
            message="success",
            data=items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Feed fetch failed: {e}", "data": None}
        )


@router.get("/tabs", response_model=StandardResponse[List[TabInfo]])
def get_tabs(client: IQIYIClient = Depends(get_client)):
    """Fetch navigation tabs."""
    try:
        tabs_data = client.get_tabs()
        tabs = [TabInfo(**tab) for tab in tabs_data]
        return StandardResponse[List[TabInfo]](
            code=200,
            message="success",
            data=tabs
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Tabs fetch failed: {e}", "data": None}
        )


@router.get("/drama/{album_id}", response_model=StandardResponse[DramaInfo])
def get_drama_detail(
    album_id: str,
    lang: str = "id_id",
    client: IQIYIClient = Depends(get_client),
):
    """Fetch detailed metadata for a drama series."""
    if not album_id or album_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 400, "message": "Invalid album_id", "data": None}
        )
    
    try:
        drama_data = client.get_drama_info(album_id, lang=lang)
        drama = DramaInfo(**drama_data)
        return StandardResponse[DramaInfo](
            code=200,
            message="success",
            data=drama
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Drama fetch failed: {e}", "data": None}
        )


@router.get("/drama/{album_id}/episodes", response_model=StandardResponse[List[EpisodeInfo]])
def get_episodes(album_id: str, client: IQIYIClient = Depends(get_client)):
    """Fetch episode list for a drama series."""
    if not album_id or album_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 400, "message": "Invalid album_id", "data": None}
        )
    
    try:
        episodes_data = client.get_episodes(album_id)
        episodes = [EpisodeInfo(**ep) for ep in episodes_data]
        return StandardResponse[List[EpisodeInfo]](
            code=200,
            message="success",
            data=episodes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": f"Episodes fetch failed: {e}", "data": None}
        )
