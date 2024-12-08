import os
import secrets
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    SecretStr,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = os.path.join(os.path.dirname(__file__), "envs/.env.dev")  # for DEV

encoding = "utf-8"
case_sensitive = True

load_dotenv(env_file)


def generate_secret(byte=512):
    return secrets.token_urlsafe(byte)


SECRET_KEY_32 = f"{generate_secret(32)}"
SECRET_KEY_64 = f"{generate_secret(64)}"


class CustomSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding=encoding,
        case_sensitive=case_sensitive,
        extra="ignore",
    )


class AppSettings(CustomSettings):
    ENVIRONMENT: Literal["local", "dev", "prod"] = Field(
        default="dev", alias="ENVIRONMENT"
    )
    DEBUG: bool = Field(default=True, alias="DEBUG")
    LOG_LEVEL: str = Field(default="DEBUG", alias="LOG_LEVEL")


class DbSettings(AppSettings):
    POSTGRES_ENGINE: str = Field(default=..., alias="POSTGRES_ENGINE")
    POSTGRES_USER: str = Field(default=..., alias="POSTGRES_USER")
    POSTGRES_PASSWORD: SecretStr = Field(default=..., alias="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default=..., alias="POSTGRES_DB")
    POSTGRES_HOST: str = Field(default=..., alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=..., alias="POSTGRES_PORT")
    DATABASE_URL: PostgresDsn | str = Field(default=..., alias="DATABASE_URL")

    @model_validator(mode="before")
    def validate_postgres_dsn(cls, data: dict):
        _built_uri = PostgresDsn.build(
            scheme=data.setdefault("POSTGRES_ENGINE", "postgresql+asyncpg"),
            username=data.setdefault("POSTGRES_USER", "postgres"),
            password=data.setdefault("POSTGRES_PASSWORD", "postgres"),
            host=data.setdefault("POSTGRES_HOST", "localhost"),
            port=int(data.setdefault("POSTGRES_PORT", 5432)),
            path=data.setdefault("POSTGRES_DB", "postgres"),
        ).unicode_string()
        data["DATABASE_URL"] = (
            _built_uri if not data.get("DATABASE_URL") else data["DATABASE_URL"]
        )
        return data


class ApiSettings(CustomSettings):
    API_V1_PREFIX: str = "/api/v1"
    API_KEY: SecretStr = Field(default=f"{SECRET_KEY_32}")
    API_SECRET: SecretStr = Field(default=f"{SECRET_KEY_32}")


class S3Settings(CustomSettings):
    AWS_ACCESS_KEY: SecretStr = Field(default="")
    AWS_SECRET_KEY: SecretStr = Field(default="")
    AWS_REGION: SecretStr = Field(default="")
    AWS_BUCKET_NAME: SecretStr = Field(default="")


class JWTSettings(CustomSettings):
    JWT_ACCESS_SECRET: SecretStr = Field(default=f"{SECRET_KEY_64}")
    JWT_ALGORITHM: str = Field(default="HS256")
    VERIFICATION_MINUTES: int = Field(default=30)
    AUDIENCE: str = Field(default="simulacrum")


class ApiCallSettings(AppSettings):
    ...

    @model_validator(mode="after")
    def validate_url(self):
        _ENV = self.ENVIRONMENT
        return self


class Settings(BaseModel):
    APP_SETTINGS: AppSettings = Field(default_factory=AppSettings)
    DATABASE: DbSettings = Field(default_factory=DbSettings)
    API_V1: ApiSettings = Field(default_factory=ApiSettings)
    S3: S3Settings = Field(default_factory=S3Settings)
    JWT: JWTSettings = Field(default_factory=JWTSettings)
    API_CALL: ApiCallSettings = Field(default_factory=ApiCallSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


SETTINGS = get_settings()
