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

db_settings = DatabaseSettings()
security_settings = SecuritySettings()
redis_settings = RedisSettings()
