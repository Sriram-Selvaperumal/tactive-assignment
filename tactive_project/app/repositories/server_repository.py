"""
ServerRepository — all MongoDB operations for the servers collection.

Responsibility:
  - CRUD operations only.
  - No business logic.
  - Returns domain model objects (Server), never raw dicts.

Design note: Methods receive a db handle rather than calling get_db()
internally so that the repository is easily testable with a mock/test db.
"""

from __future__ import annotations
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.models.server import Server, ServerStatus


class ServerRepository:
    COLLECTION = "servers"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]

    # ------------------------------------------------------------------ #
    # Write operations                                                     #
    # ------------------------------------------------------------------ #

    def create(self, server: Server) -> Server:
        """
        Persist a new server document.

        Raises DuplicateKeyError if a server with the same name exists.
        """
        doc = {
            "name": server.name,
            "cpu_capacity": server.cpu_capacity,
            "ram_capacity": server.ram_capacity,
            "server_type": server.server_type,
            "status": server.status.value,
            "allocated_cpu": server.allocated_cpu,
            "allocated_ram": server.allocated_ram,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = self._col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return Server.from_doc(doc)

    def increment_allocated_resources(
        self, server_id: str, cpu_delta: int, ram_delta: int
    ) -> bool:
        """
        Atomically increment allocated CPU and RAM for a server.

        Returns True if a document was matched and updated.
        Used during successful workload allocation.
        """
        oid = self._to_oid(server_id)
        if oid is None:
            return False
        result = self._col.update_one(
            {"_id": oid},
            {
                "$inc": {"allocated_cpu": cpu_delta, "allocated_ram": ram_delta},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        return result.matched_count == 1

    # ------------------------------------------------------------------ #
    # Read operations                                                      #
    # ------------------------------------------------------------------ #

    def get_by_id(self, server_id: str) -> Server | None:
        oid = self._to_oid(server_id)
        if oid is None:
            return None
        doc = self._col.find_one({"_id": oid})
        return Server.from_doc(doc) if doc else None

    def get_all(self) -> list[Server]:
        return [Server.from_doc(doc) for doc in self._col.find().sort("created_at", 1)]

    def get_online(self) -> list[Server]:
        """Return all servers currently in ONLINE status."""
        cursor = self._col.find({"status": ServerStatus.ONLINE.value}).sort("created_at", 1)
        return [Server.from_doc(doc) for doc in cursor]

    def update_status(self, server_id: str, status: ServerStatus) -> bool:
        """Update only the status of a server."""
        oid = self._to_oid(server_id)
        if oid is None:
            return False
        result = self._col.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.matched_count == 1

    def delete(self, server_id: str) -> bool:
        """Permanently delete a server."""
        oid = self._to_oid(server_id)
        if oid is None:
            return False
        result = self._col.delete_one({"_id": oid})
        return result.deleted_count == 1

    def reset_resources(self, server_id: str) -> bool:
        """Reset allocated CPU and RAM to 0."""
        oid = self._to_oid(server_id)
        if oid is None:
            return False
        result = self._col.update_one(
            {"_id": oid},
            {
                "$set": {
                    "allocated_cpu": 0,
                    "allocated_ram": 0,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.matched_count == 1

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_oid(id_str: str) -> ObjectId | None:
        """Convert a string to ObjectId; return None on invalid format."""
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
