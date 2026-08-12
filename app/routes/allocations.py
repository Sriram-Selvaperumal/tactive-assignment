"""
Allocation routes.

Responsibility: HTTP request/response only.
  - Validate payload.
  - Call AllocationService.
  - Map service exceptions to HTTP responses.
"""

from __future__ import annotations
import logging

from flask import Blueprint, request, current_app

from app.repositories.server_repository import ServerRepository
from app.repositories.workload_repository import WorkloadRepository
from app.repositories.allocation_repository import AllocationRepository
from app.services.allocation_service import (
    AllocationService,
    WorkloadNotFoundError,
    WorkloadAlreadyAllocatedError,
    NoEligibleServerError,
)
from app.validators import validate_allocation_payload
from app.errors import success, error

logger = logging.getLogger(__name__)
bp = Blueprint("allocations", __name__)


def _service() -> AllocationService:
    db = current_app.db
    return AllocationService(
        server_repo=ServerRepository(db),
        workload_repo=WorkloadRepository(db),
        allocation_repo=AllocationRepository(db),
    )


# ------------------------------------------------------------------ #
# POST /api/allocations                                                #
# ------------------------------------------------------------------ #

@bp.post("/api/allocations")
def create_allocation():
    """
    Submit a workload for allocation.

    Body (JSON):
        workload_id   string   required

    Responses:
        201  Allocation successful. Body includes allocation, workload, server.
        400  Validation failure or missing workload_id.
        404  Workload not found.
        409  Workload already allocated OR no eligible server available.
    """
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_allocation_payload(data)

    if not is_valid:
        return error("Validation failed.", 400, errors)

    try:
        result = _service().allocate(data["workload_id"].strip())
        logger.info("Allocation API success: allocation_id=%s", result.allocation.id)
        return success(result.to_dict(), 201)

    except WorkloadNotFoundError as exc:
        return error(str(exc), 404)

    except WorkloadAlreadyAllocatedError as exc:
        return error(str(exc), 409)

    except NoEligibleServerError as exc:
        return error(str(exc), 409)

    except Exception as exc:
        logger.exception("Unexpected error during allocation: %s", exc)
        return error("An unexpected error occurred during allocation.", 500)


# ------------------------------------------------------------------ #
# GET /api/allocations/<id>                                            #
# ------------------------------------------------------------------ #

@bp.get("/api/allocations/<allocation_id>")
def get_allocation(allocation_id: str):
    """
    GET /api/allocations/<id>

    Responses:
        200  Allocation found.
        404  Allocation not found.
    """
    from app.repositories.allocation_repository import AllocationRepository
    repo = AllocationRepository(current_app.db)
    allocation = repo.get_by_id(allocation_id)
    if allocation is None:
        return error(f"Allocation '{allocation_id}' not found.", 404)
    return success({"allocation": allocation.to_dict()})
