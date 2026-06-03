from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "mywastesolution"
    mongo_collection: str = "profiles"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
