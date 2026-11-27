from pydantic import BaseSettings


class Settings(BaseSettings): 
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    BMKG_FORECAST_BASE_URL: str
    BMKG_NOWCAST_BASE_URL: str

    class Config: 
        env_file = '.env'

settings = Settings()