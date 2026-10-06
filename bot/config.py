import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(default="YOUR_BOT_TOKEN_HERE")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:password@localhost:5432/youth_bot")
    ADMIN_IDS_RAW: str = Field(default="", alias="ADMIN_IDS")
    SUPERADMIN_IDS_RAW: str = Field(default="1202082857", alias="SUPERADMIN_IDS")
    
    # Webhook
    USE_WEBHOOK: bool = Field(default=False)
    WEBHOOK_HOST: str = Field(default="https://yoshlar.akhu.uz")
    WEBHOOK_PATH: str = Field(default="/webhook")
    WEBHOOK_SECRET: str = Field(default="secret_webhook_token")
    WEB_SERVER_HOST: str = Field(default="0.0.0.0")
    WEB_SERVER_PORT: int = Field(default=8000)
    
    # Storage and Limits
    MAX_FILE_SIZE: int = Field(default=52428800)  # 50 MB
    TIMEZONE: str = Field(default="Asia/Tashkent")
    LOG_LEVEL: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> List[int]:
        ids = []
        if self.ADMIN_IDS_RAW:
            for item in self.ADMIN_IDS_RAW.split(","):
                item = item.strip()
                if item.isdigit():
                    ids.append(int(item))
        # Ensure superadmins are always included in admin_ids
        for sa in self.superadmin_ids:
            if sa not in ids:
                ids.append(sa)
        return ids

    @property
    def superadmin_ids(self) -> List[int]:
        if not self.SUPERADMIN_IDS_RAW:
            return [1202082857]
        ids = []
        for item in self.SUPERADMIN_IDS_RAW.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        return ids

    @property
    def webhook_url(self) -> str:
        base = self.WEBHOOK_HOST.rstrip("/")
        path = self.WEBHOOK_PATH.lstrip("/")
        return f"{base}/{path}"


settings = Settings()
