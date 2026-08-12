"""
Workload routes.

Responsibility: HTTP request/response only.
"""

from __future__ import annotations
import logging

from flask import Blueprint, request, current_app
from pymongo.errors import DuplicateKeyError

from app.models.workload import Workload
from app.repositories.workload_repository import WorkloadRepository
from app.validators import validate_workload_payload
from app.errors import success, error

logger = logging.getLogger(__name__)
bp = Blueprint("workloads", __name__)


def _repo() -> WorkloadRepository:
    return WorkloadRepository(current_app.db)


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
