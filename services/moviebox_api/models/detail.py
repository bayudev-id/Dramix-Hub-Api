from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Staff:
    staff_id: str
    name: str
    character: str
    avatar_url: str
    detail_path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Staff':
        return cls(
            staff_id=str(data.get("staffId", "")),
            name=data.get("name", ""),
            character=data.get("character", ""),
            avatar_url=data.get("avatarUrl", ""),
            detail_path=data.get("detailPath", "")
        )

@dataclass
class Dub:
    subject_id: str
    lan_name: str
    lan_code: str
    is_original: bool
    type: int
    detail_path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dub':
        return cls(
            subject_id=str(data.get("subjectId", "")),
            lan_name=data.get("lanName", ""),
            lan_code=data.get("lanCode", ""),
            is_original=data.get("original", False),
            type=data.get("type", 0),
            detail_path=data.get("detailPath", "")
        )

@dataclass
class Season:
    season_num: int
    max_ep: int
    all_ep: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any], subject_id: str = "") -> 'Season':
        # Handle different key names
        season_num = data.get("season_num") if "season_num" in data else data.get("se", 1)
        max_ep = data.get("max_ep") if "max_ep" in data else data.get("maxEp", 0)
        all_ep_str = data.get("allEp", "")  # e.g. "61,62,63,...,80" or ""
        
        # If all_ep is empty but max_ep exists, generate the sequential string
        if not all_ep_str and max_ep > 0:
            all_ep_str = ",".join(map(str, range(1, max_ep + 1)))
            
        return cls(
            season_num=season_num,
            max_ep=max_ep,
            all_ep=all_ep_str
        )

@dataclass
class SubjectDetail:
    subject_id: str
    title: str
    description: str
    release_date: str = ""
    genre: List[str] = field(default_factory=list)
    cover: str = ""
    country_name: str = ""
    imdb_rating: str = ""
    detail_path: str = ""
    subject_type: int = 0
    stars: List[Staff] = field(default_factory=list)
    seasons: List[Season] = field(default_factory=list)
    dubs: List[Dub] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubjectDetail':
        subject = data.get("subject", {})
        subject_id = subject.get("subjectId", "")
        
        # Handle cover
        cover_data = subject.get("cover", {})
        cover_url = cover_data.get("url", "") if isinstance(cover_data, dict) else str(cover_data)

        # Handle seasons (flattened from resource)
        resource_data = data.get("resource", {})
        seasons_raw = resource_data.get("seasons", [])
        
        if not seasons_raw:
            # If no seasons found, create a default movie-style season
            seasons = [Season.from_dict({}, subject_id=subject_id)]
        else:
            seasons = [Season.from_dict(s, subject_id=subject_id) for s in seasons_raw]

        dubs = [Dub.from_dict(d) for d in subject.get("dubs", [])]
        
        # Determine prefix based on current subject_id matching a dub
        title = subject.get("title", "")
        for dub in dubs:
            if dub.subject_id == subject_id:
                # Remove common language suffixes like " [Indonesian]" or " [English]"
                import re
                title = re.sub(r'\s*\[.*?\]\s*', ' ', title).strip()
                title = f"[{dub.lan_name}] {title}"
                break

        return cls(
            subject_id=subject_id,
            title=title,
            description=subject.get("description", ""),
            release_date=subject.get("releaseDate", ""),
            genre=subject.get("genre", "").split(",") if subject.get("genre") else [],
            cover=cover_url,
            country_name=subject.get("countryName", ""),
            imdb_rating=subject.get("imdbRatingValue", "0.0"),
            detail_path=subject.get("detailPath", ""),
            subject_type=subject.get("subjectType", 0),
            stars=[Staff.from_dict(s) for s in data.get("stars", [])],
            seasons=seasons,
            dubs=dubs,
        )
