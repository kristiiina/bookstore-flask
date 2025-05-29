from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    APP_PORT: int

    class Config:
        env_file = '.env'


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(f"Ошибка загрузки настроек: {e}")

