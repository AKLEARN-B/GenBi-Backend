# app/config.py
"""
Pydantic-v2 compliant settings loader.
Keeps env-var names in ALL_CAPS yet exposes nice snake_case fields.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",          # load .env automatically
        extra="ignore",           # ignore unexpected keys
    )

    # ---- required ----------------------------------------------------------
    aws_region: str = Field(alias="AWS_REGION")
    athena_database: str = Field(alias="ATHENA_DB")
    athena_output: str = Field(alias="ATHENA_OUTPUT")

    # ---- optional (give defaults) -----------------------------------------
    athena_workgroup: str = Field("primary", alias="ATHENA_WORKGROUP")
    max_query_rows: int = Field(1_000, alias="MAX_ROWS")

settings = Settings()
