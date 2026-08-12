"""
test_allocations.py — Allocation business logic tests (V1 foundation).

These tests verify all 10 business rules and key edge cases.
"""

import pytest
from tests.conftest import make_server, make_workload


def allocate(client, workload_id):
    return client.post("/api/allocations", json={"workload_id": workload_id})


class TestHappyPath:
    def test_successful_allocation(self, client):
        s = make_server(client).get_json()["server"]
        w = make_workload(client).get_json()["workload"]

        r = allocate(client, w["id"])
        assert r.status_code == 201

        data = r.get_json()
        assert data["allocation"]["workload_id"] == w["id"]
        assert data["allocation"]["server_id"] == s["id"]
        assert data["allocation"]["status"] == "ACTIVE"

    def test_workload_becomes_allocated(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        allocate(client, w["id"])

        r = client.get(f"/api/workloads/{w['id']}")
        assert r.get_json()["workload"]["status"] == "ALLOCATED"

    def test_server_resources_updated(self, client):
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        make_workload(client, cpu=4, ram=8192)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        allocate(client, w["id"])

        r = client.get(f"/api/servers/{s['id']}")
        srv = r.get_json()["server"]
        assert srv["allocated_cpu"] == 4
        assert srv["allocated_ram"] == 8192
        assert srv["available_cpu"] == 12
        assert srv["available_ram"] == 24576

    def test_exact_boundary_allocation(self, client):
        """Requested resources exactly equal available — must succeed."""
        make_server(client, cpu=8, ram=16384)
        make_workload(client, cpu=8, ram=16384)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 201


class TestRejectionCases:
    def test_offline_server_ignored(self, client):
        """OFFLINE server must never receive a workload."""
        make_server(client, status="OFFLINE")
        make_workload(client)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_maintenance_server_ignored(self, client):
        make_server(client, status="MAINTENANCE")
        make_workload(client)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_insufficient_cpu_rejected(self, client):
        make_server(client, cpu=2, ram=32768)
        make_workload(client, cpu=4, ram=1024)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_insufficient_ram_rejected(self, client):
        make_server(client, cpu=16, ram=1024)
        make_workload(client, cpu=1, ram=8192)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_both_insufficient_rejected(self, client):
        make_server(client, cpu=1, ram=512)
        make_workload(client, cpu=8, ram=8192)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_server_resources_unchanged_after_rejection(self, client):
        """Rule 5 — failed allocation must not change server resources."""
        s = make_server(client, cpu=1, ram=512).get_json()["server"]
        make_workload(client, cpu=8, ram=8192)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        allocate(client, w["id"])  # will fail

        r = client.get(f"/api/servers/{s['id']}")
        srv = r.get_json()["server"]
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0

    def test_duplicate_allocation_rejected(self, client):
        """Rule 6 — an already-ALLOCATED workload cannot be reallocated."""
        make_server(client)
        make_workload(client)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        allocate(client, w["id"])           # first — succeeds
        r = allocate(client, w["id"])       # second — must fail
        assert r.status_code == 409

    def test_nonexistent_workload_returns_404(self, client):
        r = allocate(client, "000000000000000000000000")
        assert r.status_code == 404

    def test_missing_workload_id_returns_400(self, client):
        r = client.post("/api/allocations", json={})
        assert r.status_code == 400


class TestBestFitStrategy:
    def test_best_fit_selects_tighter_server(self, client):
        """
        Two ONLINE servers:
          server-A: 16 CPU, 32768 MB RAM
          server-B:  8 CPU, 16384 MB RAM

        Workload: 4 CPU, 8192 MB
        Best fit should select server-B (smaller remaining capacity).
        """
        make_server(client, name="server-a", cpu=16, ram=32768)
        b = make_server(client, name="server-b", cpu=8, ram=16384).get_json()["server"]
        make_workload(client, cpu=4, ram=8192)
        w = client.get("/api/workloads").get_json()["workloads"][0]
        r = allocate(client, w["id"])
        assert r.status_code == 201
        assert r.get_json()["allocation"]["server_id"] == b["id"]
