"""
Allocation domain model.

Records the link between a workload and the server it was placed on.
One allocation per workload (enforced by unique index on workload_id).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AllocationStatus(str, Enum):
    ACTIVE = "ACTIVE"


@dataclass
class Allocation:
    workload_id: str
    server_id: str
    status: AllocationStatus = AllocationStatus.ACTIVE
    id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workload_id": self.workload_id,
            "server_id": self.server_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def from_doc(doc: dict[str, Any]) -> "Allocation":
        return Allocation(
            id=str(doc["_id"]),
            workload_id=str(doc["workload_id"]),
            server_id=str(doc["server_id"]),
            status=AllocationStatus(doc.get("status", AllocationStatus.ACTIVE)),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
        )
