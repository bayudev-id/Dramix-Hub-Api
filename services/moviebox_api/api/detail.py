from typing import Dict, Any
from core.client import MovieBoxClient
from models.detail import SubjectDetail

class DetailAPI:
    def __init__(self, client: MovieBoxClient):
        self.client = client
        self.endpoint = "/wefeed-h5api-bff/detail"

    def get_detail(self, detail_path: str = "", subject_id: str = "") -> SubjectDetail:
        """Fetch movie details by its detail path or subject ID.
        
        If only subjectId is provided and the main endpoint fails,
        it will fallback to fetching from recommendations endpoint.
        """
        full_res = self.get_detail_raw(detail_path, subject_id)
        # Extract only the 'data' part for normalization
        data = full_res.get("data", full_res)
        
        # Check if this is a simplified structure from detail-rec endpoint
        # detail-rec returns flat structure without nested "subject" and "resource"
        if "subject" not in data and "subjectId" in data:
            # Convert detail-rec format to detail format
            data = self._convert_detail_rec_to_detail(data)
        
        return SubjectDetail.from_dict(data)

    def get_detail_raw(self, detail_path: str = "", subject_id: str = "") -> Dict[str, Any]:
        """Fetch FULL RAW movie details data (including code, message, etc).
        
        IMPORTANT: The /detail endpoint REQUIRES detailPath parameter.
        subjectId alone will return 404 error.
        
        If only subjectId is provided:
        - Returns error message instructing user to use detailPath
        - Suggests using /recommendations endpoint or search to find detailPath
        """
        # Validate parameters
        if not detail_path and not subject_id:
            raise ValueError("Either detail_path or subject_id must be provided")
        
        # If only subjectId without detailPath
        if subject_id and not detail_path:
            raise Exception(
                f"Cannot fetch detail with subjectId={subject_id} only. "
                f"The /detail endpoint requires 'detailPath' parameter. "
                f"\n\nTo get detailPath:"
                f"\n1. Use search endpoint: /search?keyword=<movie_name>"
                f"\n2. Use recommendations endpoint: /recommendations?subjectId={subject_id}"
                f"\n3. Each movie result contains 'detailPath' field"
                f"\n\nThen call: /detail?detailPath=<path_from_search>"
            )
        
        # Use detailPath (the correct way)
        params = {"detailPath": detail_path}
        return self.client.get_full(self.endpoint, params=params)

    def get_recommendations(self, subject_id: str, page: int = 1, per_page: int = 12) -> Dict[str, Any]:
        """Fetch related subjects/recommendations.
        
        This endpoint works well with subjectId and returns a list of related movies.
        Each movie in the result has both subjectId and detailPath.
        """
        params = {
            "subjectId": subject_id,
            "page": page,
            "perPage": per_page
        }
        return self.client.get("/wefeed-h5api-bff/subject/detail-rec", params=params)
    
    def get_by_subject_id_only(self, subject_id: str) -> Dict[str, Any]:
        """Fetch movie info using ONLY subjectId via detail-rec endpoint.
        
        This is a workaround when detailPath is not available.
        Returns the first recommended movie (which might be related, not exact match).
        For exact match, use detailPath parameter instead.
        """
        rec_data = self.get_recommendations(subject_id, page=1, per_page=1)
        items = rec_data.get("items", [])
        
        if not items:
            raise Exception(f"No data found for subjectId {subject_id}")
        
        return items[0]
    
    def _convert_detail_rec_to_detail(self, rec_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert detail-rec item format to detail format.
        
        detail-rec returns flat structure like:
        {
            "subjectId": "...",
            "title": "...",
            "cover": {"url": "..."},
            ...
        }
        
        detail endpoint expects nested structure like:
        {
            "subject": {
                "subjectId": "...",
                "title": "...",
                ...
            },
            "resource": {
                "seasons": [...]
            }
        }
        """
        return {
            "subject": {
                "subjectId": rec_item.get("subjectId", ""),
                "title": rec_item.get("title", ""),
                "description": rec_item.get("description", ""),
                "releaseDate": rec_item.get("releaseDate", ""),
                "genre": rec_item.get("genre", ""),
                "cover": rec_item.get("cover", {}),
                "countryName": rec_item.get("countryName", ""),
                "imdbRatingValue": rec_item.get("imdbRatingValue", "0.0"),
                "detailPath": rec_item.get("detailPath", ""),
                "subjectType": rec_item.get("subjectType", 0),
                "dubs": rec_item.get("dubs", [])
            },
            "resource": {
                "seasons": []  # detail-rec doesn't provide season info
            },
            "stars": rec_item.get("staffList", [])
        }

