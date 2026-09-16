"""Configuracoes da aplicacao, lidas de variaveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variaveis de ambiente da atelie-api."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://atelie:atelie@db:5432/atelie"
    cors_origins: str = "http://localhost:3000"
    # Placeholder de MVP academico: nao e autenticacao. Ver README.
    admin_token: str = "dev-token"
    media_dir: str = "/app/media"
    viacep_base_url: str = "https://viacep.com.br/ws"
    viacep_timeout_seconds: float = 5.0

    @property
    def cors_origin_list(self) -> list[str]:
        """Converte a lista de origens separadas por virgula em lista."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retorna as configuracoes em cache."""
    return Settings()
