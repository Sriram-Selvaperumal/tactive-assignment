"""
Centralized error handling and response helpers.

Design decision:
  - Business errors (AllocationError subclasses) map to explicit HTTP codes.
  - Unexpected exceptions (500) are logged with full traceback but return
    a safe generic message — never leak internals to the client.
  - All error responses use the same JSON envelope: {error, message, details?}
"""

from __future__ import annotations
import logging

from flask import Flask, jsonify
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Response helpers                                                     #
# ------------------------------------------------------------------ #

def success(data: dict | list, status: int = 200):
    return jsonify(data), status


def error(message: str, status: int, details: list[str] | None = None):
    body = {"error": True, "message": message}
    if details:
        body["details"] = details
    return jsonify(body), status


# ------------------------------------------------------------------ #
# Flask error handlers                                                 #
# ------------------------------------------------------------------ #

def register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(e):
        return error(str(e), 400)

    @app.errorhandler(404)
    def not_found(e):
        return error("The requested resource was not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error("Method not allowed.", 405)

    @app.errorhandler(409)
    def conflict(e):
        return error(str(e), 409)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Unhandled server error: %s", e)
        return error("An unexpected error occurred. Please try again.", 500)
