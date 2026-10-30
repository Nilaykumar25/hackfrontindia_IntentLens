from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "neo4j+s://localhost"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    github_token: str = ""
    repo_owner: str = "redis"
    repo_name: str = "redis"
    repo_local_path: str = "data/repo"
    subsystem_paths: str = "src/replication.c,src/rdb.c,src/aof.c,redis.conf"
    max_prs: int = 400
    max_commits: int = 3000

    llm_provider: str = "sarvam"
    llm_model: str = "claude-sonnet-5-5"
    anthropic_api_key: str = ""
    sarvam_api_key: str = ""
    sarvam_model: str = "sarvam-105b"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    cache_dir: str = "data/cache"
    max_graph_hops: int = 3
    refusal_threshold: float = 0.35
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def paths(self) -> list[str]:
        return [p.strip() for p in self.subsystem_paths.split(",") if p.strip()]


settings = Settings()
