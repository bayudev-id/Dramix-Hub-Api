from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Image:
    url: str
    width: int
    height: int
    format: str

@dataclass
class SubjectMovie:
    subject_id: str
    detail_path: str
    subject_type: int
    title: str
    release_date: str
    genre: List[str]
    country_name: str
    imdb_rating: str
    corner: str
    cover: str
    banner_image: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubjectMovie':
        cover = data.get("cover", {})
        return cls(
            subject_id=data.get("subjectId", ""),
            detail_path=data.get("detailPath", ""),
            subject_type=data.get("subjectType", 0),
            title=data.get("title", ""),
            release_date=data.get("releaseDate", ""),
            genre=data.get("genre", "").split(",") if data.get("genre") else [],
            country_name=data.get("countryName", ""),
            imdb_rating=str(data.get("imdbRatingValue", "0")),
            corner=data.get("corner", ""),
            cover=cover.get("url", "") if isinstance(cover, dict) else str(cover),
            banner_image=data.get("banner_image")
        )

@dataclass
class BannerItem:
    id: str
    title: str
    cover: str
    detail_path: str
    subject: Optional[SubjectMovie] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BannerItem':
        image = data.get("image", {})
        subject_data = data.get("subject")
        subject = SubjectMovie.from_dict(subject_data) if subject_data else None
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            cover=image.get("url", ""),
            detail_path=data.get("detailPath", ""),
            subject=subject
        )

@dataclass
class FilterItem:
    title: str
    query: str
    cover: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterItem':
        image = data.get("image", {})
        return cls(
            title=data.get("title", ""),
            query=data.get("query", ""),
            cover=image.get("url", "")
        )

@dataclass
class UpcomingMovie(SubjectMovie):
    appointment_date: str = ""
    appointment_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpcomingMovie':
        base = SubjectMovie.from_dict(data)
        return cls(
            subject_id=base.subject_id,
            detail_path=base.detail_path,
            subject_type=base.subject_type,
            title=base.title,
            release_date=base.release_date,
            genre=base.genre,
            country_name=base.country_name,
            imdb_rating=base.imdb_rating,
            corner=base.corner,
            cover=base.cover,
            appointment_date=data.get("appointmentDate", ""),
            appointment_count=data.get("appointmentCnt", 0)
        )

@dataclass
class LiveSportMatch:
    match_id: str
    team1_name: str
    team1_score: str
    team2_name: str
    team2_score: str
    start_time: str
    status: str
    url: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiveSportMatch':
        team1 = data.get("team1", {})
        team2 = data.get("team2", {})
        return cls(
            match_id=data.get("matchId", ""),
            team1_name=team1.get("nameTag", ""),
            team1_score=str(team1.get("score", "0")),
            team2_name=team2.get("nameTag", ""),
            team2_score=str(team2.get("score", "0")),
            start_time=data.get("startTime", ""),
            status=data.get("status", ""),
            url=data.get("url", "")
        )

@dataclass
class HomeSection:
    type: str
    title: str
    position: int
    raw_data: Dict[str, Any]

@dataclass
class HomeData:
    platforms: List[Dict[str, Any]]
    sections: List[HomeSection]

@dataclass
class Pager:
    has_more: bool
    next_page: str
    page: str
    per_page: int
    total_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pager':
        return cls(
            has_more=data.get("hasMore", False),
            next_page=data.get("nextPage", ""),
            page=data.get("page", "0"),
            per_page=data.get("perPage", 18),
            total_count=data.get("totalCount", 0)
        )

@dataclass
class TrendingResponse:
    subjects: List[SubjectMovie]
    pager: Optional[Pager]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendingResponse':
        subjects = [SubjectMovie.from_dict(item) for item in data.get("subjectList", [])]
        pager_data = data.get("pager", {})
        pager = Pager.from_dict(pager_data) if pager_data else None
        return cls(subjects=subjects, pager=pager)
