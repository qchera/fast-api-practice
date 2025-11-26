from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
        env_file='.env',
        env_ignore_empty=True,
        extra='ignore'
    )

class DatabaseSettings(BaseSettings):
    POSTGRES_PASSWORD: str = ""
    POSTGRES_USERNAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    DB_NAME: str

    model_config = _base_config

    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USERNAME}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.DB_NAME}"

class SecuritySettings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    model_config = _base_config

class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    model_config = _base_config

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

class EmailNotificationSettings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    model_config = _base_config

db_settings = DatabaseSettings()
security_settings = SecuritySettings()
redis_settings = RedisSettings()
email_notification_settings = EmailNotificationSettings()
