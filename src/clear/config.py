"""Runtime configuration for Clear."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    master_secret: str
    operator_token: str
    currency_name: str = "Clear Mint Units"
    mint_url: str = "http://127.0.0.1:3339"
    max_order: int = 20
    root_authority_npub: str | None = None
    currency_alias: str | None = None
    currency_unit_alias: str | None = None
    key_encryption_key: str | None = None
    root_api_loopback_only: bool = True

    def __post_init__(self) -> None:
        if len(self.master_secret) < 32:
            raise ValueError("master_secret must contain at least 32 characters")
        if len(self.operator_token) < 24:
            raise ValueError("operator_token must contain at least 24 characters")
        if not 1 <= self.max_order <= 30:
            raise ValueError("max_order must be between 1 and 30")

    @classmethod
    def from_env(cls) -> Settings:
        env_file = Path.cwd() / ".env"
        if env_file.is_file():
            load_dotenv(env_file, override=False)

        master_secret = os.getenv("CLEAR_MASTER_SECRET", "")
        operator_token = os.getenv("CLEAR_OPERATOR_TOKEN", "")
        if not master_secret or not operator_token:
            raise RuntimeError(
                "CLEAR_MASTER_SECRET and CLEAR_OPERATOR_TOKEN must be configured"
            )
        return cls(
            database_path=Path(
                os.getenv("CLEAR_DATABASE", "./data/clear.sqlite3")
            ).expanduser(),
            master_secret=master_secret,
            operator_token=operator_token,
            currency_name=os.getenv("CLEAR_CURRENCY_NAME", "Clear Mint Units"),
            mint_url=os.getenv("CLEAR_MINT_URL", "http://127.0.0.1:3339").rstrip("/"),
            max_order=int(os.getenv("CLEAR_MAX_ORDER", "20")),
            root_authority_npub=os.getenv("CLEAR_ROOT_AUTHORITY_NPUB") or None,
            currency_alias=os.getenv("CLEAR_CURRENCY_ALIAS") or None,
            currency_unit_alias=os.getenv("CLEAR_CURRENCY_UNIT_ALIAS") or None,
            key_encryption_key=os.getenv("CLEAR_KEY_ENCRYPTION_KEY") or None,
        )
