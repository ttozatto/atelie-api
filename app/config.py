"""Configuracoes da aplicacao, lidas de variaveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variaveis de ambiente da atelie-api."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Obrigatorias e sem valor padrao: nenhum segredo fica escrito no codigo. Sem elas a
    # API nao sobe, em vez de subir com uma credencial conhecida.
    database_url: str
    # Placeholder de MVP academico: nao e autenticacao. Ver README.
    admin_token: str
    cors_origins: str = "http://localhost:3000"
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
