"""Response models and domain schemas for iQIYI API."""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standardized REST response envelope."""
    code: int = Field(default=200, description="HTTP-like response status code")
    message: str = Field(default="success", description="Status or error message")
    data: Optional[T] = Field(default=None, description="Response payload")


class EpisodeInfo(BaseModel):
    """Metadata for a single drama episode."""
    episode_number: int = Field(description="Sequential episode index")
    title: str = Field(default="", description="Episode title")
    duration: Optional[int] = Field(default=None, description="Duration in seconds")
    is_vip: bool = Field(default=False, description="Whether episode requires VIP")
    subtitles: List[str] = Field(default_factory=list, description="Available subtitle language codes")
    video_id: Optional[str] = Field(default=None, description="Upstream video/item ID")


class CastMember(BaseModel):
    """Person involved in drama production (actor, director)."""
    id: Optional[str] = Field(default=None, description="Upstream star / celebrity ID")
    name: str = Field(description="Full name of person")
    image: Optional[str] = Field(default=None, description="Avatar or portrait photo URL")
    role: Optional[str] = Field(default=None, description="Role label (e.g. Sutradara, Pemeran Utama)")

    @model_validator(mode="before")
    @classmethod
    def parse_str(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data}
        return data


class CoverImages(BaseModel):
    """Collection of vertical and horizontal cover images in multiple dimensions."""
    vertical: Optional[str] = Field(default=None, description="Portrait poster image URL (3:4 ratio)")
    horizontal: Optional[str] = Field(default=None, description="Landscape banner/backdrop image URL (16:9 ratio)")


class DramaInfo(BaseModel):
    """Detailed metadata for a drama series."""
    id: str = Field(description="Unique album or series ID")
    name: str = Field(description="Title of the drama")
    desc: Optional[str] = Field(default="", description="Synopsis or description")
    cover: Optional[str] = Field(default="", description="Primary portrait poster image URL (vertical)")
    banner: Optional[str] = Field(default=None, description="Primary landscape banner/backdrop image URL (horizontal)")
    covers: Optional[CoverImages] = Field(default=None, description="Detailed vertical and horizontal covers")
    genre: Optional[str] = Field(default="", description="Genre label")
    badges: List[str] = Field(default_factory=list, description="Header overview badges, e.g., ['Original', '9.6', '13+', '2021', '24 Episode']")
    tags: List[str] = Field(default_factory=list, description="Categorical and genre tags, e.g., ['China Daratan', 'Idol', 'Percintaan']")
    year: Optional[int] = Field(default=None, description="Release year")
    vip_status: bool = Field(default=False, description="Whether series is VIP-only")
    total_episodes: Optional[int] = Field(default=None, description="Total episode count")
    score: Optional[str] = Field(default=None, description="Audience rating score, e.g., '9.6'")
    score_votes: Optional[int] = Field(default=None, description="Total audience rating vote count")
    rating: Optional[str] = Field(default=None, description="Content age rating, e.g., '13+'")
    directors: List[CastMember] = Field(default_factory=list, description="List of directors with photos")
    main_actors: List[CastMember] = Field(default_factory=list, description="List of main cast actors with photos")
    is_original: bool = Field(default=False, description="Whether produced or exclusive to iQIYI")
    categories: Optional[Dict[str, List[str]]] = Field(default=None, description="Detailed category tag mapping")


class SearchResult(BaseModel):
    """Container for paginated search results."""
    keyword: str
    pg_num: int
    has_more: bool = False
    items: List[DramaInfo] = Field(default_factory=list)


class FeedItem(BaseModel):
    """Container for a single curated homepage item."""
    id: str
    name: str
    cover: Optional[str] = None
    banner: Optional[str] = None
    covers: Optional[CoverImages] = None
    desc: Optional[str] = None
    badge: Optional[str] = None
    is_vip: bool = False


class TabInfo(BaseModel):
    """Metadata for a homepage navigation tab."""
    tab_key: str
    name: str
    module_key: Optional[str] = None


class LoginRequest(BaseModel):
    """Payload for POST /api/auth/login."""
    username: str
    password: str


class AuthStatusData(BaseModel):
    """Data payload for auth status check."""
    is_active: bool
    vip_status: bool
    account_identifier: Optional[str] = None
    vip_type: Optional[str] = None
    created_at: Optional[str] = None


class StreamQuality(BaseModel):
    """Metadata and direct stream URL for a specific video quality tier."""
    quality: str = Field(description="Resolution label, e.g., 360p, 720p, 1080p")
    bid: int = Field(description="iQIYI bitrate ID, e.g., 200, 500, 600")
    format: str = Field(default="m3u8", description="Stream format (m3u8, ts, mpd)")
    url: str = Field(description="Direct playable CDN stream URL")
    is_vip: bool = Field(default=False, description="Whether this quality requires VIP status")


class SubtitleItem(BaseModel):
    """Metadata and direct file URL for a subtitle track."""
    language: str = Field(description="Full display language name, e.g., Bahasa Indonesia")
    lang_code: str = Field(description="ISO language code, e.g., id, en, zh-CN")
    format: str = Field(default="webvtt", description="Subtitle format (webvtt, srt)")
    url: str = Field(description="Direct CDN or proxy URL to subtitle file")


class AudioTrackItem(BaseModel):
    """Metadata for an alternative or dubbing audio track."""
    name: str = Field(description="Track name or display label, e.g., Original, Indonesian Dub")
    lang_code: str = Field(description="ISO language code, e.g., zh, id")
    is_default: bool = Field(default=False, description="Whether this is the default track")


class PlaybackData(BaseModel):
    """Complete playback payload for a video episode."""
    tv_id: str = Field(description="Unique video/item identifier")
    album_id: Optional[str] = Field(default=None, description="Album or series identifier")
    duration: int = Field(default=0, description="Video duration in seconds")
    is_vip_applied: bool = Field(default=False, description="Whether VIP credentials were applied")
    streams: List[StreamQuality] = Field(default_factory=list, description="List of available stream qualities")
    subtitles: List[SubtitleItem] = Field(default_factory=list, description="Available subtitle tracks")
    audio_tracks: List[AudioTrackItem] = Field(default_factory=list, description="Available audio tracks")


class PlaybackResponse(StandardResponse[PlaybackData]):
    """Standardized response envelope for playback data."""
    data: Optional[PlaybackData] = None

