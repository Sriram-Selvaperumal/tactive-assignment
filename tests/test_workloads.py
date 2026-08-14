"""
test_workloads.py — Workload endpoint tests.

Covers:
  - Creation: valid, invalid, duplicate, boundary values
  - Listing
  - Retrieval: found, not found, invalid ID
"""

import pytest
from tests.conftest import make_workload


class TestCreateWorkload:

    # ---------------------------------------------------------------- #
    # Happy path                                                         #
    # ---------------------------------------------------------------- #

    def test_create_valid_workload(self, client):
        r = make_workload(client, name="job-01", cpu=4, ram=8192)
        assert r.status_code == 201
        w = r.get_json()["workload"]
        assert w["name"] == "job-01"
        assert w["cpu_required"] == 4
        assert w["ram_required"] == 8192
        assert w["status"] == "PENDING"
        assert w["id"] is not None

    def test_workload_starts_as_pending(self, client):
        r = make_workload(client)
        assert r.get_json()["workload"]["status"] == "PENDING"

    # ---------------------------------------------------------------- #
    # Name validation                                                    #
    # ---------------------------------------------------------------- #

    def test_missing_name_rejected(self, client):
        r = client.post("/api/workloads", json={"cpu_required": 4, "ram_required": 8192})
        assert r.status_code == 400

    def test_empty_name_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "", "cpu_required": 4, "ram_required": 8192})
        assert r.status_code == 400

    def test_whitespace_only_name_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "   ", "cpu_required": 4, "ram_required": 8192})
        assert r.status_code == 400

    def test_duplicate_name_rejected(self, client):
        make_workload(client, name="job-01")
        r = make_workload(client, name="job-01")
        assert r.status_code == 409

    # ---------------------------------------------------------------- #
    # CPU validation                                                     #
    # ---------------------------------------------------------------- #

    def test_missing_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "ram_required": 1024})
        assert r.status_code == 400

    def test_zero_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 0, "ram_required": 1024})
        assert r.status_code == 400

    def test_negative_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": -1, "ram_required": 1024})
        assert r.status_code == 400

    def test_float_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 2.5, "ram_required": 1024})
        assert r.status_code == 400

    def test_string_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": "four", "ram_required": 1024})
        assert r.status_code == 400

    def test_bool_cpu_rejected(self, client):
        """Boolean must not be accepted as integer."""
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": True, "ram_required": 1024})
        assert r.status_code == 400

    def test_excessive_cpu_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 99999, "ram_required": 1024})
        assert r.status_code == 400

    # ---------------------------------------------------------------- #
    # RAM validation                                                     #
    # ---------------------------------------------------------------- #

    def test_missing_ram_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 4})
        assert r.status_code == 400

    def test_zero_ram_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 4, "ram_required": 0})
        assert r.status_code == 400

    def test_negative_ram_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 4, "ram_required": -512})
        assert r.status_code == 400

    def test_excessive_ram_rejected(self, client):
        r = client.post("/api/workloads", json={"name": "job-x", "cpu_required": 4, "ram_required": 9999999})
        assert r.status_code == 400

    # ---------------------------------------------------------------- #
    # Boundary values                                                    #
    # ---------------------------------------------------------------- #

    def test_minimum_valid_values(self, client):
        """cpu=1, ram=1 should be accepted."""
        r = client.post("/api/workloads", json={"name": "min-job", "cpu_required": 1, "ram_required": 1})
        assert r.status_code == 201

    def test_maximum_valid_values(self, client):
        r = client.post("/api/workloads", json={"name": "max-job", "cpu_required": 10000, "ram_required": 1048576})
        assert r.status_code == 201

    # ---------------------------------------------------------------- #
    # Malformed request                                                  #
    # ---------------------------------------------------------------- #

    def test_empty_body_rejected(self, client):
        r = client.post("/api/workloads", json={})
        assert r.status_code == 400

    def test_no_json_content_type(self, client):
        r = client.post("/api/workloads", data="not json")
        assert r.status_code == 400


class TestListWorkloads:

    def test_empty_list(self, client):
        r = client.get("/api/workloads")
        assert r.status_code == 200
        data = r.get_json()
        assert data["workloads"] == []
        assert data["count"] == 0

    def test_lists_all_workloads(self, client):
        make_workload(client, name="job-01")
        make_workload(client, name="job-02")
        make_workload(client, name="job-03")
        r = client.get("/api/workloads")
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] == 3
        assert len(data["workloads"]) == 3


class TestGetWorkload:

    def test_get_existing_workload(self, client):
        created = make_workload(client, name="job-01").get_json()["workload"]
        r = client.get(f"/api/workloads/{created['id']}")
        assert r.status_code == 200
        assert r.get_json()["workload"]["name"] == "job-01"

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/api/workloads/000000000000000000000000")
        assert r.status_code == 404

    def test_invalid_id_format_returns_404(self, client):
        r = client.get("/api/workloads/not-a-valid-id")
        assert r.status_code == 404
