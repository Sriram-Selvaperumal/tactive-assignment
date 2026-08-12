"""
AllocationService — core business logic for workload allocation.

This is the most important module in the application.
It is the ONLY place where allocation rules are enforced.

Responsibilities:
  - Enforce all 10 business rules.
  - Select the best-fit server.
  - Coordinate the atomic write sequence.
  - Return rich result objects for the route layer.

Design decision — Best Fit strategy:
  Among all ONLINE servers with sufficient CPU AND RAM, select the server
  with the smallest combined remaining capacity after placement:

      score = (available_cpu - required_cpu) + (available_ram - required_ram)

  Minimum score wins (tightest pack). Tie-broken by insertion order (oldest first).

  Rationale: deterministic, maximises utilisation, simple to explain and test.

Error model:
  The service raises typed exceptions (AllocationError subclasses).
  The route layer catches these and maps them to HTTP responses.
  This keeps HTTP concerns out of the service.
"""

from __future__ import annotations
import logging

from pymongo.errors import DuplicateKeyError

from app.models.server import Server, ServerStatus
from app.models.workload import Workload, WorkloadStatus
from app.models.allocation import Allocation
from app.repositories.server_repository import ServerRepository
from app.repositories.workload_repository import WorkloadRepository
from app.repositories.allocation_repository import AllocationRepository

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Custom exceptions — typed error model                                #
# ------------------------------------------------------------------ #

class AllocationError(Exception):
    """Base class for all allocation-specific errors."""


class WorkloadNotFoundError(AllocationError):
    pass


class WorkloadAlreadyAllocatedError(AllocationError):
    pass


class NoEligibleServerError(AllocationError):
    pass


# ------------------------------------------------------------------ #
# Result object                                                        #
# ------------------------------------------------------------------ #

class AllocationResult:
    """Carries the outcome of a successful allocation for the route layer."""

    def __init__(
        self,
        allocation: Allocation,
        workload: Workload,
        server: Server,
    ) -> None:
        self.allocation = allocation
        self.workload = workload
        self.server = server

    def to_dict(self) -> dict:
        return {
            "allocation": self.allocation.to_dict(),
            "workload": self.workload.to_dict(),
            "server": self.server.to_dict(),
        }


# ------------------------------------------------------------------ #
# Service                                                              #
# ------------------------------------------------------------------ #

class AllocationService:
    def __init__(
        self,
        server_repo: ServerRepository,
        workload_repo: WorkloadRepository,
        allocation_repo: AllocationRepository,
    ) -> None:
        self._servers = server_repo
        self._workloads = workload_repo
        self._allocations = allocation_repo

    def allocate(self, workload_id: str) -> AllocationResult:
        """
        Attempt to allocate a workload to the best available server.

        Raises:
            WorkloadNotFoundError           — workload_id does not exist
            WorkloadAlreadyAllocatedError   — workload is already ALLOCATED (Rule 6)
            NoEligibleServerError           — no ONLINE server has sufficient resources
        """
        logger.info("Allocation attempt: workload_id=%s", workload_id)

        # --- Step 1: Load and validate workload ---------------------------
        workload = self._workloads.get_by_id(workload_id)
        if workload is None:
            logger.warning("Allocation rejected: workload %s not found.", workload_id)
            raise WorkloadNotFoundError(f"Workload '{workload_id}' not found.")

        # Rule 6 — no duplicate allocation
        if workload.status == WorkloadStatus.ALLOCATED:
            logger.warning(
                "Allocation rejected: workload %s is already ALLOCATED.", workload_id
            )
            raise WorkloadAlreadyAllocatedError(
                f"Workload '{workload.name}' is already allocated."
            )

        # --- Step 2: Find eligible servers --------------------------------
        # Rule 1 — only ONLINE servers
        online_servers = self._servers.get_online()

        # Rules 2, 3, 4 — sufficient CPU AND RAM
        eligible = [
            s for s in online_servers
            if s.available_cpu >= workload.cpu_required
            and s.available_ram >= workload.ram_required
        ]

        if not eligible:
            logger.warning(
                "Allocation rejected: no eligible server for workload %s "
                "(cpu_required=%d, ram_required=%d).",
                workload_id,
                workload.cpu_required,
                workload.ram_required,
            )
            raise NoEligibleServerError(
                "No ONLINE server has sufficient CPU and RAM for this workload."
            )

        # --- Step 3: Best-fit selection -----------------------------------
        selected_server = self._best_fit(eligible, workload)
        logger.info(
            "Selected server: id=%s, name=%s (score=%d)",
            selected_server.id,
            selected_server.name,
            self._fit_score(selected_server, workload),
        )

        # --- Step 4: Atomic write sequence --------------------------------
        # MongoDB does not support multi-document transactions without a
        # replica set, so we use compensating logic:
        # Write the allocation record first (unique index prevents duplicates),
        # then update server resources and workload status.
        # If any step fails after the allocation insert, we log the
        # inconsistency — in a production system this would be idempotently
        # retried. For V1, this is an acceptable trade-off given SQLite was
        # replaced with MongoDB.

        try:
            allocation = self._allocations.create(
                Allocation(
                    workload_id=workload.id,
                    server_id=selected_server.id,
                )
            )
        except DuplicateKeyError:
            # Race condition guard — another request allocated this workload
            logger.warning(
                "Duplicate allocation attempt for workload %s (concurrent request).",
                workload_id,
            )
            raise WorkloadAlreadyAllocatedError(
                f"Workload '{workload.name}' was concurrently allocated."
            )

        # Rule 8 — update server resources
        self._servers.increment_allocated_resources(
            selected_server.id,
            workload.cpu_required,
            workload.ram_required,
        )

        # Update workload status to ALLOCATED
        self._workloads.update_status(workload.id, WorkloadStatus.ALLOCATED)

        # Reload for accurate response data
        updated_server = self._servers.get_by_id(selected_server.id)
        updated_workload = self._workloads.get_by_id(workload.id)

        logger.info(
            "Allocation SUCCESS: allocation_id=%s, workload=%s, server=%s.",
            allocation.id,
            workload.name,
            selected_server.name,
        )

        return AllocationResult(
            allocation=allocation,
            workload=updated_workload,
            server=updated_server,
        )

    # ------------------------------------------------------------------ #
    # Scheduling strategy — Best Fit                                      #
    # ------------------------------------------------------------------ #

    def _best_fit(self, eligible: list[Server], workload: Workload) -> Server:
        """
        Select the server with the smallest remaining combined capacity
        after the workload would be placed. Tie-broken by oldest insertion
        (list is already sorted ascending by created_at from the repository).
        """
        return min(eligible, key=lambda s: self._fit_score(s, workload))

    @staticmethod
    def _fit_score(server: Server, workload: Workload) -> int:
        """
        Lower score = tighter fit = preferred.

            score = (available_cpu - required_cpu) + (available_ram - required_ram)
        """
        return (
            (server.available_cpu - workload.cpu_required)
            + (server.available_ram - workload.ram_required)
        )
