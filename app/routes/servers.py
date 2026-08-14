"""
Server routes.

Responsibility: HTTP request/response only.
  - Parse and validate input.
  - Call the repository.
  - Return formatted JSON response.
  - No business logic here.
"""

from __future__ import annotations
import logging

from flask import Blueprint, request, current_app
from pymongo.errors import DuplicateKeyError

from app.models.server import Server, ServerStatus
from app.repositories import ServerRepository, WorkloadRepository, AllocationRepository
from app.services import AllocationService, ServerNotFoundError, AllocationError
from app.validators import validate_server_payload
from app.errors import success, error

logger = logging.getLogger(__name__)
bp = Blueprint("servers", __name__)


def _repo() -> ServerRepository:
    return ServerRepository(current_app.db)


def _service() -> AllocationService:
    db = current_app.db
    return AllocationService(
        server_repo=_repo(),
        workload_repo=WorkloadRepository(db),
        allocation_repo=AllocationRepository(db),
    )


# ------------------------------------------------------------------ #
# POST /api/servers                                                    #
# ------------------------------------------------------------------ #

@bp.post("/api/servers")
def create_server():
    """
    Create a new server.

    Body (JSON):
        name          string   required
        cpu_capacity  int      required  (cores, 1..10000)
        ram_capacity  int      required  (MB, 1..1048576)
        server_type   string   optional  default "general"
        status        string   optional  default "ONLINE"

    Responses:
        201  Server created.
        400  Validation failure.
        409  Server name already exists.
    """
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_server_payload(data)

    if not is_valid:
        return error("Validation failed.", 400, errors)

    server = Server(
        name=data["name"].strip(),
        cpu_capacity=data["cpu_capacity"],
        ram_capacity=data["ram_capacity"],
        server_type=data.get("server_type", "general").strip(),
        status=ServerStatus(data.get("status", ServerStatus.ONLINE.value)),
    )

    try:
        created = _repo().create(server)
    except DuplicateKeyError:
        return error(f"A server named '{server.name}' already exists.", 409)

    logger.info("Server created: id=%s name=%s", created.id, created.name)
    return success({"server": created.to_dict()}, 201)


# ------------------------------------------------------------------ #
# GET /api/servers                                                     #
# ------------------------------------------------------------------ #

@bp.get("/api/servers")
def list_servers():
    """
    GET /api/servers

    Returns all servers sorted by creation time.

    Responses:
        200  List of servers (may be empty).
    """
    servers = _repo().get_all()
    return success({"servers": [s.to_dict() for s in servers], "count": len(servers)})


# ------------------------------------------------------------------ #
# GET /api/servers/<id>                                                #
# ------------------------------------------------------------------ #

@bp.get("/api/servers/<server_id>")
def get_server(server_id: str):
    """
    GET /api/servers/<id>

    Responses:
        200  Server found.
        404  Server not found or invalid ID.
    """
    server = _repo().get_by_id(server_id)
    if server is None:
        return error(f"Server '{server_id}' not found.", 404)
    return success({"server": server.to_dict()})


# ------------------------------------------------------------------ #
# PATCH /api/servers/<server_id>/status                                #
# ------------------------------------------------------------------ #

@bp.patch("/api/servers/<server_id>/status")
def update_server_status(server_id: str):
    """
    Update the status of a server.
    """
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status or not isinstance(status, str) or not status.strip():
        return error("Status is required and must be a non-empty string.", 400)

    try:
        updated = _service().update_server_status(server_id, status.strip())
        logger.info("Server %s status updated to %s", server_id, status)
        return success({"server": updated.to_dict()}, 200)
    except ServerNotFoundError as exc:
        return error(str(exc), 404)
    except AllocationError as exc:
        return error(str(exc), 400)


# ------------------------------------------------------------------ #
# DELETE /api/servers/<server_id>                                      #
# ------------------------------------------------------------------ #

@bp.delete("/api/servers/<server_id>")
def delete_server(server_id: str):
    """
    Permanently delete a server.
    """
    try:
        _service().delete_server(server_id)
        logger.info("Server %s deleted", server_id)
        return success({"deleted": True, "server_id": server_id}, 200)
    except ServerNotFoundError as exc:
        return error(str(exc), 404)
