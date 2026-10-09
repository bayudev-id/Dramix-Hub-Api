from typing import Dict, Any, List
from core.client import MovieBoxClient
from models.search import SearchResponse
import dataclasses

class SearchAPI:
    def __init__(self, client: MovieBoxClient):
        self.client = client
        self.endpoint = "/wefeed-h5api-bff/subject/search"

    def search(self, keyword: str, page: int = 1, per_page: int = 10, subject_type: int = 0) -> SearchResponse:
        """Search for movies/dramas by keyword using POST with correct headers."""
        payload = {
            "keyword": keyword,
            "page": str(page),
            "perPage": per_page,
            "subjectType": subject_type
        }
        
        # Extract token from session cookies if self.client.token is not set
        token_val = self.client.token if self.client.token else self.client.session.cookies.get("mb_token")
        
        # Use session.post directly with proper headers matching Burp intercept
        from core.config import settings
        url = f"{settings.BASE_URL}{self.endpoint}"
        headers = {
            "Authorization": f"Bearer {token_val}" if token_val else "",
            "X-Client-Info": '{"timezone":"Asia/Jakarta"}',
            "X-Vip-Restrict": "1",
            "X-No-High-Risk-Restrict": "0",
            "X-Request-Lang": self.client.lang,
            "Origin": "https://movieboxhd.net",
            "Referer": "https://movieboxhd.net/",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Brave";v="152"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Gpc": "1",
        }
        
        import requests as raw_requests
        response = raw_requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("code") not in [0, 200]:
            raise Exception(f"API Error: {data.get('message', 'Unknown error')} (Code: {data.get('code')})")
            
        return SearchResponse.from_api_response(keyword, data)


    def suggest(self, keyword: str, per_page: int = 10) -> Dict[str, Any]:
        """Get search suggestions (keywords)."""
        payload = {
            "keyword": keyword,
            "perPage": per_page
        }
        data = self.client.post("/wefeed-h5api-bff/subject/search-suggest", json=payload)
        return data.get("items", [])
