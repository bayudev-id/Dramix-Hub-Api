from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from models.home import SubjectMovie, Pager

@dataclass
class SearchResponse:
    keyword: str
    data: List[SubjectMovie]
    pager: Optional[Pager]
    debug_raw_count: int

    @classmethod
    def from_api_response(cls, keyword: str, data: Dict[str, Any]) -> 'SearchResponse':
        # API returns: {"code": 0, "data": {"items": [...], "pager": {...}}}
        # So we need to access data["data"] first
        inner_data = data.get("data", {})
        subjects_raw = inner_data.get("items", [])
        
        # Convert search results ke SubjectMovie objects
        subjects = [SubjectMovie.from_dict(item) for item in subjects_raw]
        
        pager_data = inner_data.get("pager")
        pager = Pager.from_dict(pager_data) if pager_data else None
        
        return cls(
            keyword=keyword,
            data=subjects,
            pager=pager,
            debug_raw_count=len(subjects_raw)
        )
