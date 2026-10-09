"""Playback route handlers for stream and subtitle resolution."""
from fastapi import APIRouter, HTTPException, Query
from src.client.iqiyi_client import IQIYIClient, PlaybackError
from src.models.schemas import PlaybackResponse

router = APIRouter(prefix="/api", tags=["Playback"])
client = IQIYIClient()


@router.get("/play/{tv_id}", response_model=PlaybackResponse)
async def get_playback_by_tv_id(
    tv_id: str,
    bid: int = Query(None, description="Optional bitrate ID filter (e.g., 500 for 720p, 600 for 1080p)"),
    album_id: str = Query(None, description="Album ID for short drama")
):
    """
    Resolve playback streams, subtitles, and audio tracks for a given tv_id.
    
    Returns direct CDN URLs for multi-quality video streams, subtitle tracks (WebVTT/SRT),
    and available audio tracks. Automatically applies VIP credentials if active session exists.
    
    For mobile-exclusive short drama: provide album_id parameter.
    
    **Parameters:**
    - `tv_id`: Unique episode/video identifier
    - `bid`: Optional bitrate filter (200=360p, 300=480p, 500=720p, 600=1080p)
    - `album_id`: Album ID (triggers short drama resolver if provided)
    
    **Response:**
    - `streams`: List of available stream qualities with direct m3u8 URLs
    - `subtitles`: Available subtitle tracks with language codes
    - `audio_tracks`: Available audio/dubbing options
    - `is_vip_applied`: Whether VIP credentials were used
    """
    try:
        # If album_id provided, try short drama resolver
        if album_id:
            playback = await client.get_playback_short_drama(tv_id, album_id, bid)
            return PlaybackResponse(
                code=200,
                message="success",
                data=playback
            )
        
        # Standard drama resolver
        playback = await client.get_playback(tv_id, bid)
        return PlaybackResponse(
            code=200,
            message="success",
            data=playback
        )
    except PlaybackError as e:
        raise HTTPException(status_code=e.code or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playback resolution failed: {str(e)}")


@router.get("/drama/{album_id}/episode/{episode_number}/playback", response_model=PlaybackResponse)
async def get_playback_by_episode(
    album_id: str,
    episode_number: int,
    bid: int = Query(None, description="Optional bitrate ID filter")
):
    """
    Convenience alias: resolve playback by album_id and episode number.
    
    Automatically looks up the tv_id for the specified episode, then resolves playback.
    
    **Parameters:**
    - `album_id`: Drama series identifier
    - `episode_number`: Sequential episode number (1-based)
    - `bid`: Optional bitrate filter
    
    **Response:**
    - Same structure as `/api/play/{tv_id}`
    """
    try:
        # Lookup episode list to find tv_id
        episodes = client.get_episodes(album_id)
        target = next((ep for ep in episodes if ep.get("episode_number") == episode_number), None)
        
        if not target or not target.get("video_id"):
            raise HTTPException(
                status_code=404,
                detail=f"Episode {episode_number} not found in album {album_id}"
            )
        
        tv_id = target["video_id"]
        playback = await client.get_playback(tv_id, bid)
        
        return PlaybackResponse(
            code=200,
            message="success",
            data=playback
        )
    except HTTPException:
        raise
    except PlaybackError as e:
        raise HTTPException(status_code=e.code or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playback resolution failed: {str(e)}")
