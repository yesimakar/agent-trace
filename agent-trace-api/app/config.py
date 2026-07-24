import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://agenttrace:agenttrace@localhost:5432/agenttrace",
    )
    cors_origins: list[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            origins = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
            object.__setattr__(self, "cors_origins", [item.strip() for item in origins.split(",")])


settings = Settings()
