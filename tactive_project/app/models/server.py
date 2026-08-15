"""
Server domain model.

Represents a physical or virtual server in the data centre.
This is a pure Python dataclass — no database coupling.
Persistence is handled by ServerRepository.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ServerStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class Server:
    name: str
    cpu_capacity: int           # CPU cores
    ram_capacity: int           # RAM in MB
    server_type: str = "general"
    status: ServerStatus = ServerStatus.ONLINE
    allocated_cpu: int = 0
    allocated_ram: int = 0
    id: str | None = None       # MongoDB ObjectId as string
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------ #
    # Computed properties                                                  #
    # ------------------------------------------------------------------ #

    @property
    def available_cpu(self) -> int:
        return self.cpu_capacity - self.allocated_cpu

    @property
    def available_ram(self) -> int:
        return self.ram_capacity - self.allocated_ram

    @property
    def cpu_utilisation_pct(self) -> float:
        if self.cpu_capacity == 0:
            return 0.0
        return round((self.allocated_cpu / self.cpu_capacity) * 100, 2)

    @property
    def ram_utilisation_pct(self) -> float:
        if self.ram_capacity == 0:
            return 0.0
        return round((self.allocated_ram / self.ram_capacity) * 100, 2)

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "server_type": self.server_type,
            "status": self.status.value,
            "cpu_capacity": self.cpu_capacity,
            "ram_capacity": self.ram_capacity,
            "allocated_cpu": self.allocated_cpu,
            "allocated_ram": self.allocated_ram,
            "available_cpu": self.available_cpu,
            "available_ram": self.available_ram,
            "cpu_utilisation_pct": self.cpu_utilisation_pct,
            "ram_utilisation_pct": self.ram_utilisation_pct,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Deserialisation                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def from_doc(doc: dict[str, Any]) -> "Server":
        """Construct a Server from a raw MongoDB document."""
        return Server(
            id=str(doc["_id"]),
            name=doc["name"],
            cpu_capacity=doc["cpu_capacity"],
            ram_capacity=doc["ram_capacity"],
            server_type=doc.get("server_type", "general"),
            status=ServerStatus(doc.get("status", ServerStatus.ONLINE)),
            allocated_cpu=doc.get("allocated_cpu", 0),
            allocated_ram=doc.get("allocated_ram", 0),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        )
