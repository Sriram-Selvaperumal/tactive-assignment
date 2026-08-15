"""
Workload domain model.

Represents a compute job submitted by a user for allocation to a server.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkloadStatus(str, Enum):
    PENDING = "PENDING"
    ALLOCATED = "ALLOCATED"


@dataclass
class Workload:
    name: str
    cpu_required: int       # CPU cores requested
    ram_required: int       # RAM in MB requested
    status: WorkloadStatus = WorkloadStatus.PENDING
    id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "cpu_required": self.cpu_required,
            "ram_required": self.ram_required,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_doc(doc: dict[str, Any]) -> "Workload":
        return Workload(
            id=str(doc["_id"]),
            name=doc["name"],
            cpu_required=doc["cpu_required"],
            ram_required=doc["ram_required"],
            status=WorkloadStatus(doc.get("status", WorkloadStatus.PENDING)),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        )
