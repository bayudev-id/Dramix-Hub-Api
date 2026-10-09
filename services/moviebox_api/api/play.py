import requests as raw_requests
from typing import Dict, Any, List
from core.client import MovieBoxClient
from models.play import PlayData, Caption

class PlayAPI:
    def __init__(self, client: MovieBoxClient):
        self.client = client
        self.endpoint = "/wefeed-h5api-bff/subject/play"

    def get_play_info(self, subject_id: str, season: int = 1, episode: int = 1, detail_path: str = "") -> PlayData:
        """Fetch playback streams for a specific episode.
        
        PENTING: Endpoint play harus dipanggil TANPA cookies/Authorization apapun.
        Jika ada cookies (terutama token), server akan mengenali user dan 
        memberlakukan rate-limit (limited=true, streams kosong).
        Tanpa cookies = anonymous = freeNum 999, streams tersedia.
        """
        
        params = {
            "subjectId": subject_id,
            "se": season,
            "ep": episode,
            "detailPath": detail_path
        }
        
        # Endpoint play dipanggil via netfilm.world (same-origin seperti browser)
        url = "https://netfilm.world/wefeed-h5api-bff/subject/play"
        
        # Header untuk VIP akses (Membuka 720p)
        token_val = self.client.session.cookies.get("mb_token")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
            "Accept": "application/json",
            "Accept-Language": f"{self.client.lang},en-US;q=0.9,en;q=0.8",
            "Referer": f"https://netfilm.world/spa/videoPlayPage/movies/{detail_path}?id={subject_id}",
            "X-Client-Info": '{"timezone":"Asia/Jakarta","userType":1,"vipLevel":2,"region":"ID","sp_code":"51010","net":"NETWORK_WIFI"}',
            "X-Vip-Restrict": "0",
            "X-No-High-Risk-Restrict": "1",
            "X-Forwarded-For": "103.152.112.128",
            "X-Real-IP": "103.152.112.128",
            "X-Source": "",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        if token_val:
            headers["Authorization"] = f"Bearer {token_val}"
            headers["X-MB-Token"] = token_val
        
        # KUNCI: Gunakan requests.get() langsung, BUKAN self.client.session.get()
        # Ini menghindari pengiriman cookies (mb_token, token) dari session
        # yang menyebabkan server rate-limit user (limited=true, streams=[])
        response = raw_requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("code") not in [0, 200]:
            raise Exception(f"API Error: {data.get('message', 'Unknown error')} (Code: {data.get('code')})")
            
        return PlayData.from_dict(data.get("data", {}))

    def get_captions(self, subject_id: str, stream_id: str, format: str = "MP4", detail_path: str = "") -> List[Caption]:
        """Fetch captions/subtitles for a specific stream."""
        params = {
            "format": format,
            "id": stream_id,
            "subjectId": subject_id,
            "detailPath": detail_path
        }
        data = self.client.get("/wefeed-h5api-bff/subject/caption", params=params)
        # Note: Response has "captions" key
        return [Caption.from_dict(c) for c in data.get("captions", [])]
