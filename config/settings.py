"""Application configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="Helios", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8001, alias="API_PORT")

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5433, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="helios", alias="POSTGRES_DB")
    postgres_user: str = Field(default="helios", alias="POSTGRES_USER")
    postgres_password: str = Field(default="helios_password", alias="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Kafka/Redpanda
    kafka_bootstrap_servers: str = Field(default="localhost:19092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_schema_registry_url: str = Field(default="http://localhost:18081", alias="KAFKA_SCHEMA_REGISTRY_URL")

    # Reconciliation Settings
    reconciliation_window_seconds: int = Field(default=30, alias="RECONCILIATION_WINDOW_SECONDS")
    reconciliation_max_retries: int = Field(default=3, alias="RECONCILIATION_MAX_RETRIES")

    # Self-Healing Settings
    auto_scale_enabled: bool = Field(default=True, alias="AUTO_SCALE_ENABLED")
    lag_threshold: int = Field(default=5000, alias="LAG_THRESHOLD")
    dlq_growth_threshold: int = Field(default=100, alias="DLQ_GROWTH_THRESHOLD")
    circuit_breaker_threshold: int = Field(default=10, alias="CIRCUIT_BREAKER_THRESHOLD")

    # AWS
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_eventbridge_bus_name: str = Field(default="default", alias="AWS_EVENTBRIDGE_BUS_NAME")

    # GCP
    gcp_project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    gcp_credentials_path: Optional[str] = Field(default=None, alias="GCP_CREDENTIALS_PATH")
    gcp_pubsub_subscription: str = Field(default="helios-subscription", alias="GCP_PUBSUB_SUBSCRIPTION")

    # Azure
    azure_tenant_id: Optional[str] = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, alias="AZURE_CLIENT_SECRET")
    azure_eventgrid_topic_endpoint: Optional[str] = Field(default=None, alias="AZURE_EVENTGRID_TOPIC_ENDPOINT")

    # Observability
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3000, alias="GRAFANA_PORT")
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    jaeger_endpoint: str = Field(default="http://localhost:14268/api/traces", alias="JAEGER_ENDPOINT")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
