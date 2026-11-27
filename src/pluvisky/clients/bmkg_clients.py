import traceback
import requests

from pluvisky.config.base import settings

class BmkgClients: 
    def __init__(self):
        self.__base_url_forecast: str = settings.BMKG_FORECAST_BASE_URL
        self.__base_url_nowcast: str = settings.BMKG_NOWCAST_BASE_URL
        self.__headers: dict = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        }

    def __api_request(self, url: str) -> dict: 
        resp = requests.get(url, headers=self.__headers, timeout=30)
        if resp.status_code != 200: 
            return {"error": resp.text, "status_code": resp.status_code}
        return {"results": resp.text, "status_code": resp.status_code}

    def get_bmkg_forecast(self, subdistrict_code: str) -> str: 
        url = f"{self.__base_url_forecast}/cuaca/prakiraan-cuaca/{subdistrict_code}"
        resp = self.__api_request(url)
        
        if "error" in resp: 
            return {"url": url, "error": resp['error']}
        return {"url": url,"results": resp['results']}

    def get_bmkg_nowcast(self) -> str: 
        resp = self.__api_request(
            self.__base_url_nowcast
        )
        return resp
    