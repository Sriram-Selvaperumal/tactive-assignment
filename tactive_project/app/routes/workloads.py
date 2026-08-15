"""
Workload routes.

Responsibility: HTTP request/response only.
"""

from __future__ import annotations
import logging

from flask import Blueprint, request, current_app
from pymongo.errors import DuplicateKeyError

from app.models.workload import Workload
from app.repositories import ServerRepository, WorkloadRepository, AllocationRepository
from app.services import AllocationService, WorkloadNotFoundError, AllocationError
from app.validators import validate_workload_payload
from app.errors import success, error

logger = logging.getLogger(__name__)
bp = Blueprint("workloads", __name__)


def _repo() -> WorkloadRepository:
    return WorkloadRepository(current_app.db)


def _service() -> AllocationService:
    db = current_app.db
    return AllocationService(
        server_repo=ServerRepository(db),
        workload_repo=_repo(),
        allocation_repo=AllocationRepository(db),
    )


# ------------------------------------------------------------------ #
# POST /api/workloads                                                  #
# ------------------------------------------------------------------ #

@bp.post("/api/workloads")
def create_workload():
    """
    Create a new workload (starts in PENDING status).

    Body (JSON):
        name          string   required
        cpu_required  int      required  (cores, 1..10000)
        ram_required  int      required  (MB, 1..1048576)

    Responses:
        201  Workload created.
        400  Validation failure.
        409  Workload name already exists.
    """
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_workload_payload(data)

    if not is_valid:
        return error("Validation failed.", 400, errors)

    workload = Workload(
        name=data["name"].strip(),
        cpu_required=data["cpu_required"],
        ram_required=data["ram_required"],
    )

    try:
        created = _repo().create(workload)
    except DuplicateKeyError:
        return error(f"A workload named '{workload.name}' already exists.", 409)

    logger.info("Workload created: id=%s name=%s", created.id, created.name)
    return success({"workload": created.to_dict()}, 201)


# ------------------------------------------------------------------ #
# GET /api/workloads                                                   #
# ------------------------------------------------------------------ #

@bp.get("/api/workloads")
def list_workloads():
    workloads = _repo().get_all()
    return success({"workloads": [w.to_dict() for w in workloads], "count": len(workloads)})


# ------------------------------------------------------------------ #
# GET /api/workloads/<id>                                              #
# ------------------------------------------------------------------ #

@bp.get("/api/workloads/<workload_id>")
def get_workload(workload_id: str):
    workload = _repo().get_by_id(workload_id)
    if workload is None:
        return error(f"Workload '{workload_id}' not found.", 404)
    return success({"workload": workload.to_dict()})


# ------------------------------------------------------------------ #
# PATCH /api/workloads/<workload_id>                                   #
# ------------------------------------------------------------------ #

@bp.patch("/api/workloads/<workload_id>")
def update_workload_resources(workload_id: str):
    """
    Modify CPU cores or RAM required by a workload.
    """
    data = request.get_json(silent=True) or {}
    cpu = data.get("cpu_required")
    ram = data.get("ram_required")
    errors = []

    if cpu is None:
        errors.append("'cpu_required' is required.")
    elif not isinstance(cpu, int) or isinstance(cpu, bool) or cpu < 1 or cpu > 10000:
        errors.append("'cpu_required' must be an integer between 1 and 10000.")

    if ram is None:
        errors.append("'ram_required' is required.")
    elif not isinstance(ram, int) or isinstance(ram, bool) or ram < 1 or ram > 1048576:
        errors.append("'ram_required' must be an integer between 1 and 1048576.")

    if errors:
        return error("Validation failed.", 400, errors)

    try:
        updated = _service().update_workload_resources(workload_id, cpu, ram)
        logger.info("Workload %s resources updated (CPU: %s, RAM: %s)", workload_id, cpu, ram)
        return success({"workload": updated.to_dict()}, 200)
    except WorkloadNotFoundError as exc:
        return error(str(exc), 404)
    except AllocationError as exc:
        return error(str(exc), 409)


# ------------------------------------------------------------------ #
# DELETE /api/workloads/<workload_id>                                  #
# ------------------------------------------------------------------ #

@bp.delete("/api/workloads/<workload_id>")
def delete_workload(workload_id: str):
    """
    Permanently delete a workload.
    """
    try:
        _service().delete_workload(workload_id)
        logger.info("Workload %s deleted", workload_id)
        return success({"deleted": True, "workload_id": workload_id}, 200)
    except WorkloadNotFoundError as exc:
        return error(str(exc), 404)
