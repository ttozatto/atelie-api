"""Configuracoes da aplicacao, lidas de variaveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variaveis de ambiente da atelie-api."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Obrigatorias e sem valor padrao: nenhum segredo fica escrito no codigo. Sem elas a
    # API nao sobe, em vez de subir com uma credencial conhecida.
    database_url: str
    # Credenciais do painel. Placeholder de MVP academico: um unico usuario fixo, sem
    # banco de usuarios, sem hash de senha e sem expiracao. Ver README.
    admin_password: str
    admin_token: str
    admin_username: str = "admin"
    # Armazenamento de objetos compativel com S3 (RustFS no compose, S3 na AWS).
    s3_access_key: str
    s3_secret_key: str
    s3_endpoint_url: str = "http://storage:9000"
    s3_bucket: str = "atelie-media"
    s3_region: str = "us-east-1"
    cors_origins: str = "http://localhost:3000"
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
