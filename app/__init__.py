"""
Application factory.

create_app() is the single entry point for constructing a Flask application.

Benefits of the factory pattern:
  - Enables testing with an isolated in-memory database (TestingConfig).
  - Avoids circular imports by deferring all wiring to call time.
  - Makes the app explicit and configurable without global state.
"""

from __future__ import annotations
import logging
import logging.config

from flask import Flask, render_template

from app.config import get_config
from app.database import init_db
from app.routes import register_blueprints
from app.errors import register_error_handlers


def create_app(config=None) -> Flask:
    """
    Construct and configure the Flask application.

    Args:
        config: A config class, string env name, or None (reads APP_ENV from env).

    Returns:
        A fully configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # ---------------------------------------------------------------- #
    # 1. Load configuration                                             #
    # ---------------------------------------------------------------- #
    if config is None:
        config = get_config()
    elif isinstance(config, str):
        config = get_config(config)

    app.config.from_object(config)

    # ---------------------------------------------------------------- #
    # 2. Configure logging                                              #
    # ---------------------------------------------------------------- #
    _configure_logging(app)

    # ---------------------------------------------------------------- #
    # 3. Initialise database connection                                 #
    # ---------------------------------------------------------------- #
    init_db(app)

    # ---------------------------------------------------------------- #
    # 4. Register blueprints (routes)                                   #
    # ---------------------------------------------------------------- #
    register_blueprints(app)

    # ---------------------------------------------------------------- #
    # 5. Register error handlers                                        #
    # ---------------------------------------------------------------- #
    register_error_handlers(app)

    # ---------------------------------------------------------------- #
    # 6. Frontend route                                                  #
    # ---------------------------------------------------------------- #
    @app.get("/")
    def index():
        return render_template("index.html")

    app.logger.info(
        "Application started. env=%s db=%s",
        app.config.get("ENV", "development"),
        app.config.get("MONGO_DBNAME"),
    )

    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
