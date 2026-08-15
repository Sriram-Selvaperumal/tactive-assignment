"""
Application configuration.

Three environments are defined:
  DevelopmentConfig  — local MongoDB, debug on
  TestingConfig      — isolated test database, debug off
  ProductionConfig   — placeholder (not used in V1)

The active config is selected via the APP_ENV environment variable.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Shared defaults for all environments."""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DBNAME: str = os.getenv("MONGO_DBNAME", "datacenter_db")
    JSON_SORT_KEYS: bool = False


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    MONGO_DBNAME: str = os.getenv("MONGO_DBNAME", "datacenter_db")


class TestingConfig(BaseConfig):
    TESTING: bool = True
    DEBUG: bool = False
    MONGO_DBNAME: str = "datacenter_test_db"   # Separate DB — never pollutes dev data


class ProductionConfig(BaseConfig):
    DEBUG: bool = False


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env: str | None = None):
    """Return the config class for the given environment name."""
    env = env or os.getenv("APP_ENV", "development")
    return _CONFIG_MAP.get(env, DevelopmentConfig)
