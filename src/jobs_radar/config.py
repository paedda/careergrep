"""Configuration loading from config.yaml."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class UserConfig(BaseModel):
    name: str
    profile_summary: str


class KeywordsConfig(BaseModel):
    must_have_any: list[str] = []
    nice_to_have: list[str] = []
    exclude: list[str] = []


class CompaniesConfig(BaseModel):
    greenhouse: list[str] = []
    lever: list[str] = []
    ashby: list[str] = []
    workable: list[str] = []


class FiltersConfig(BaseModel):
    max_age_hours: int = 24
    min_score: int = 3


class EmailConfig(BaseModel):
    enabled: bool = True
    to: str = ""
    from_: str = ""  # 'from' is a Python keyword
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587


class ClaudeConfig(BaseModel):
    enabled: bool = False
    model: str = "claude-sonnet-4-6"
    daily_budget_usd: float = 2.0


class DeliveryConfig(BaseModel):
    email: EmailConfig = EmailConfig()


class Settings(BaseModel):
    user: UserConfig
    keywords: KeywordsConfig = KeywordsConfig()
    companies: CompaniesConfig = CompaniesConfig()
    filters: FiltersConfig = FiltersConfig()
    delivery: DeliveryConfig = DeliveryConfig()
    claude: ClaudeConfig = ClaudeConfig()


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from config.yaml.

    Looks in the project root by default. In PHP you'd typically use
    an array or .env — Python favors structured config with validation,
    which is what Pydantic gives us here.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text())

    # Handle 'from' key — it's a Python reserved word, so we map it manually
    if "delivery" in raw and "email" in raw["delivery"]:
        email = raw["delivery"]["email"]
        if "from" in email:
            email["from_"] = email.pop("from")

    return Settings(**raw)
