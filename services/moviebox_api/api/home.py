from typing import List, Dict, Any
from core.client import MovieBoxClient
from models.home import (
    HomeData, HomeSection, BannerItem, FilterItem, 
    SubjectMovie, UpcomingMovie, LiveSportMatch,
    TrendingResponse
)

class HomeAPI:
    def __init__(self, client: MovieBoxClient):
        self.client = client
        self.endpoint = "/wefeed-h5api-bff/home"

    def get_raw_home(self) -> Dict[str, Any]:
        """Fetch raw home data from API."""
        return self.client.get(self.endpoint)

    def get_home(self) -> HomeData:
        """Fetch and parse home data into basic sections."""
        data = self.get_raw_home()
        platforms = data.get("platformList", [])
        sections = []
        
        for item in data.get("operatingList", []):
            section = HomeSection(
                type=item.get("type", ""),
                title=item.get("title", ""),
                position=item.get("position", 0),
                raw_data=item
            )
            sections.append(section)
            
        return HomeData(platforms=platforms, sections=sections)

    def get_banners(self) -> List[BannerItem]:
        """Extract banner items from home data."""
        home_data = self.get_home()
        banners = []
        for section in home_data.sections:
            if section.type == "BANNER":
                banner_data = section.raw_data.get("banner", {})
                if banner_data:
                    for item in banner_data.get("items", []):
                        banners.append(BannerItem.from_dict(item))
        return banners

    def get_filters(self) -> List[FilterItem]:
        """Extract filter categories from home data."""
        home_data = self.get_home()
        filters = []
        for section in home_data.sections:
            if section.type == "FILTER":
                for item in section.raw_data.get("filters", []):
                    filters.append(FilterItem.from_dict(item))
        return filters

    def get_movie_sections(self) -> Dict[str, List[SubjectMovie]]:
        """Extract all movie sections mapped by their title."""
        home_data = self.get_home()
        movie_sections = {}
        for section in home_data.sections:
            if section.type == "SUBJECTS_MOVIE":
                title = section.title
                subjects = [SubjectMovie.from_dict(s) for s in section.raw_data.get("subjects", [])]
                movie_sections[title] = subjects
        return movie_sections

    def get_upcoming_movies(self) -> List[UpcomingMovie]:
        """Extract upcoming appointments/movies."""
        home_data = self.get_home()
        upcoming = []
        for section in home_data.sections:
            if section.type == "APPOINTMENT_LIST":
                for item in section.raw_data.get("subjects", []):
                    upcoming.append(UpcomingMovie.from_dict(item))
        return upcoming

    def get_live_sports(self) -> List[LiveSportMatch]:
        """Extract live sport matches."""
        home_data = self.get_home()
        live_sports = []
        for section in home_data.sections:
            if section.type == "SPORT_LIVE":
                for item in section.raw_data.get("liveList", []):
                    live_sports.append(LiveSportMatch.from_dict(item))
        return live_sports

    def get_trending(self, page: int = 0, per_page: int = 18) -> TrendingResponse:
        """Fetch trending (Saran) subjects.
        
        Args:
            page: the page number
            per_page: items per page (default 18)
            
        Returns:
            TrendingResponse containing list of subjects and pager info (isMore)
        """
        params = {"page": page, "perPage": per_page, "host": None}
        data = self.client.get("/wefeed-h5api-bff/subject/trending", params=params)
        return TrendingResponse.from_dict(data)

    def get_ranking_content(self, ranking_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Fetch ranking list content via web API (h5-api.aoneroom.com).
        
        Args:
            ranking_id: ID dari ranking list (contoh: '8821254238245470240')
            page: halaman (dimulai dari 1)
            per_page: jumlah item per halaman
        """
        params = {
            "id": ranking_id,
            "page": page,
            "perPage": per_page
        }
        return self.client.get("/wefeed-h5api-bff/ranking-list/content", params=params)

    def get_operational_content(self, op_id: str) -> Dict[str, Any]:
        """Fetch content for a specific operational ID (like Banners) by searching Home sections."""
        home_data = self.get_home()
        for section in home_data.sections:
            if section.raw_data.get("opId") == op_id:
                # Handle BANNER type specifically
                if section.type == "BANNER":
                    items = section.raw_data.get("banner", {}).get("items", [])
                    subjects_with_images = []
                    for item in items:
                        subj = item.get("subject")
                        if subj:
                            # Tambahkan field banner_image ke dalam data subject
                            subj["banner_image"] = item.get("image", {}).get("url", "")
                            subjects_with_images.append(subj)
                    return {
                        "title": section.title,
                        "type": section.type,
                        "data": subjects_with_images
                    }
                # Handle other types (SLOT, etc)
                return {
                    "title": section.title,
                    "type": section.type,
                    "data": section.raw_data.get("subjects", [])
                }
        return {"error": "opId not found", "data": []}

