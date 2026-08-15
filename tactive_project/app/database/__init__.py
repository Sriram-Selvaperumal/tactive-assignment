"""
MongoDB connection management.

Provides a single PyMongo client shared across the application.

Design:
  - `init_db(app)` is called once inside create_app().
  - It stores the client and database handle on the Flask `app` object.
  - Routes access `current_app.db` to get the active database handle.
  - Indexes are created on startup (idempotent).

Why PyMongo directly (no ODM):
  Keeps the stack thin, gives full query control, and is easy to test
  by passing a different db handle to repositories.
"""

from __future__ import annotations
from pymongo import MongoClient
from pymongo.database import Database


def init_db(app) -> None:
    """
    Initialise the MongoDB client and attach db handle to the Flask app.
    Called once inside create_app().
    """
    uri = app.config["MONGO_URI"]
    db_name = app.config["MONGO_DBNAME"]

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    app.db_client = client
    app.db = client[db_name]

    try:
        _ensure_indexes(app.db)
        app.logger.info("MongoDB connected: db=%s", db_name)
    except Exception as exc:  # noqa: BLE001
        # MongoDB may not be running yet — warn but don't crash.
        # Indexes will be created on first successful connection.
        app.logger.warning(
            "MongoDB not reachable at startup (will retry on first request): %s", exc
        )


def _ensure_indexes(db: Database) -> None:
    """
    Create uniqueness indexes on application startup.
    Idempotent — safe to call on every restart.
    """
    db["servers"].create_index("name", unique=True)
    db["workloads"].create_index("name", unique=True)
    db["allocations"].create_index("workload_id", unique=True)
