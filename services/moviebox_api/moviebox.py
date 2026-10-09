from core.client import MovieBoxClient, MovieBoxAPIException
from api.home import HomeAPI
from api.search import SearchAPI
from api.detail import DetailAPI
from api.play import PlayAPI

class MovieBox:
    """
    Main client for interacting with MovieBox API.
    
    Usage:
        client = MovieBox(token="your_token_here")
        banners = client.home.get_banners()
        for banner in banners:
            print(banner.title)
    """
    def __init__(self, token: str = None, lang: str = "id"):
        self.client = MovieBoxClient(token=token, lang=lang)
        self.home = HomeAPI(self.client)
        self.search = SearchAPI(self.client)
        self.detail = DetailAPI(self.client)
        self.play = PlayAPI(self.client)

    def set_lang(self, lang: str):
        """Change API language."""
        self.client.set_lang(lang)


__all__ = ["MovieBox", "MovieBoxAPIException"]
