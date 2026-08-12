"""
AllocationRepository — all MongoDB operations for the allocations collection.
"""

from __future__ import annotations
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from app.models.allocation import Allocation, AllocationStatus


class AllocationRepository:
    COLLECTION = "allocations"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]

    def create(self, allocation: Allocation) -> Allocation:
        doc = {
            "workload_id": allocation.workload_id,
            "server_id": allocation.server_id,
            "status": allocation.status.value,
            "created_at": datetime.now(timezone.utc),
        }
        result = self._col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return Allocation.from_doc(doc)

    def get_by_id(self, allocation_id: str) -> Allocation | None:
        oid = self._to_oid(allocation_id)
        if oid is None:
            return None
        doc = self._col.find_one({"_id": oid})
        return Allocation.from_doc(doc) if doc else None

    def get_by_workload_id(self, workload_id: str) -> Allocation | None:
        """Return the allocation for a given workload (at most one exists)."""
        doc = self._col.find_one({"workload_id": workload_id})
        return Allocation.from_doc(doc) if doc else None

    @staticmethod
    def _to_oid(id_str: str) -> ObjectId | None:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
