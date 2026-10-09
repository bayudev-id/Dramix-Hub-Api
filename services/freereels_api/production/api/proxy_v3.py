#!/usr/bin/env python3
"""
FreeReels API Proxy v3 - Simple wrapper around FreeReelsClient
Production version.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from core.client import FreeReelsClient

app = FastAPI(
    title="FreeReels API Proxy v3",
    description="Production HTTP wrapper around FreeReelsClient",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client: Optional[FreeReelsClient] = None

def get_client() -> FreeReelsClient:
    global _client
    if not _client:
        _client = FreeReelsClient()
        _client.login_anonymous()
    return _client

class FeedRequest(BaseModel):
    module_key: str
    offset: int = 0
    clean: bool = True

class FeedResponse(BaseModel):
    code: int
    message: str
    data: Dict[str, Any]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/feed", response_model=FeedResponse)
async def get_feed(req: FeedRequest):
    try:
        client = get_client()
        dramas = client.get_tab_feed(
            module_key=req.module_key,
            offset=req.offset,
            clean=req.clean
        )
        return FeedResponse(
            code=200,
            message="success",
            data={
                "items": dramas,
                "count": len(dramas),
                "offset": req.offset,
                "module_key": req.module_key,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ranking")
async def get_ranking(period: str = "daily"):
    try:
        client = get_client()
        ranking = client.get_ranking(key=period)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "period": period,
                "items": ranking,
                "count": len(ranking),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/detail")
@app.get("/drama/info_v2")
async def get_detail(id: str = None, series_id: str = None, episode_id: str = None, episode: int = None):
    """Get drama detail info or episode playback
    
    FreeReels API returns all episodes in data.info.episode_list, but data.info.episode is always Episode 1.
    This endpoint finds the requested episode in episode_list and puts it in data.info.episode.
    
    Params:
        episode_id: Episode UUID (e.g., "GgaWqRsJaB")
        episode: Episode number (1, 2, 3...)
    """
    try:
        if not id and not series_id:
            raise HTTPException(status_code=400, detail="Missing id or series_id parameter")
        
        series_id = series_id or id
        client = get_client()
        
        # Get full detail (contains all episodes in episode_list)
        detail = client.get_video_detail(series_id=series_id)
        
        if not detail:
            raise HTTPException(status_code=404, detail="Drama not found")
        
        # If episode_id or episode number provided, find it in episode_list
        if (episode_id or episode) and "info" in detail and "episode_list" in detail["info"]:
            episode_list = detail["info"]["episode_list"]
            
            if episode_id:
                # Find by ID
                found = next((ep for ep in episode_list if ep.get("id") == episode_id), None)
                if found:
                    detail["info"]["episode"] = found
                    print(f"[INFO] Selected episode by ID: {episode_id} -> {found.get('name')}")
                else:
                    print(f"[WARN] Episode ID {episode_id} not found in episode_list")
            elif episode:
                # Find by number (1-indexed)
                idx = episode - 1
                if 0 <= idx < len(episode_list):
                    detail["info"]["episode"] = episode_list[idx]
                    print(f"[INFO] Selected episode by number: {episode} -> {episode_list[idx].get('name')}")
                else:
                    print(f"[WARN] Episode number {episode} out of range (1-{len(episode_list)})")
        
        # Wrap response for frontend compatibility
        return {
            "code": 200,
            "message": "success",
            "data": detail
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
