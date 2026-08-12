"""
WorkloadRepository — all MongoDB operations for the workloads collection.
"""

from __future__ import annotations
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from app.models.workload import Workload, WorkloadStatus


class WorkloadRepository:
    COLLECTION = "workloads"

    def __init__(self, db: Database) -> None:
        self._col = db[self.COLLECTION]

    def create(self, workload: Workload) -> Workload:
        doc = {
            "name": workload.name,
            "cpu_required": workload.cpu_required,
            "ram_required": workload.ram_required,
            "status": workload.status.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = self._col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return Workload.from_doc(doc)

    def get_by_id(self, workload_id: str) -> Workload | None:
        oid = self._to_oid(workload_id)
        if oid is None:
            return None
        doc = self._col.find_one({"_id": oid})
        return Workload.from_doc(doc) if doc else None

    def get_all(self) -> list[Workload]:
        return [Workload.from_doc(doc) for doc in self._col.find().sort("created_at", 1)]

    def update_status(self, workload_id: str, status: WorkloadStatus) -> bool:
        """
        Update workload status (e.g. PENDING → ALLOCATED).
        Returns True when a document was matched.
        """
        oid = self._to_oid(workload_id)
        if oid is None:
            return False
        result = self._col.update_one(
            {"_id": oid},
            {"$set": {"status": status.value, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.matched_count == 1

    @staticmethod
    def _to_oid(id_str: str) -> ObjectId | None:
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
