"""Health check route."""
from datetime import datetime, timezone
from flask import Blueprint
from app.errors import success

bp = Blueprint("health", __name__)


@bp.get("/api/health")
def health():
    """
    GET /api/health

    Returns 200 with server timestamp.
    Used by the frontend on load to confirm API reachability.
    """
    return success({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Data Centre Resource Allocation API",
        "version": "1.1",
    })
