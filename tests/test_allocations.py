"""
test_allocations.py — Comprehensive allocation edge case tests.

Covers ALL 10 business rules + boundary conditions + error paths.
These are the AI-generated test scripts for V1.1 documentation.

Rule mapping:
  Rule 1  — Only ONLINE servers eligible
  Rule 2  — CPU capacity must not be exceeded
  Rule 3  — RAM capacity must not be exceeded
  Rule 4  — BOTH CPU and RAM must be satisfied
  Rule 5  — Failed allocation leaves resources unchanged
  Rule 6  — No duplicate allocation
  Rule 7  — Deterministic Best Fit selection
  Rule 8  — Resources correctly updated after allocation
  Rule 9  — Allocation, workload status, server resources consistent
  Rule 10 — Invalid requests rejected before allocation logic
"""

import pytest
from tests.conftest import make_server, make_workload


def allocate(client, workload_id):
    return client.post("/api/allocations", json={"workload_id": workload_id})


def get_server(client, server_id):
    return client.get(f"/api/servers/{server_id}").get_json()["server"]


def get_workload(client, workload_id):
    return client.get(f"/api/workloads/{workload_id}").get_json()["workload"]


# ====================================================================
# HAPPY PATH
# ====================================================================

class TestHappyPath:

    def test_successful_allocation_returns_201(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201

    def test_response_contains_allocation_id(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.get_json()["allocation"]["id"] is not None

    def test_response_contains_correct_workload_id(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.get_json()["allocation"]["workload_id"] == w["id"]

    def test_response_contains_server_id(self, client):
        s = make_server(client).get_json()["server"]
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.get_json()["allocation"]["server_id"] == s["id"]

    def test_allocation_status_is_active(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.get_json()["allocation"]["status"] == "ACTIVE"

    def test_response_includes_workload_details(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        data = r.get_json()
        assert "workload" in data
        assert data["workload"]["id"] == w["id"]

    def test_response_includes_server_details(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        data = r.get_json()
        assert "server" in data


# ====================================================================
# RULE 1 — Only ONLINE servers eligible
# ====================================================================

class TestRule1ServerStatus:

    def test_offline_server_not_allocated(self, client):
        """Rule 1: OFFLINE server must be ignored."""
        make_server(client, name="offline-node", status="OFFLINE")
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_maintenance_server_not_allocated(self, client):
        """Rule 1: MAINTENANCE server must be ignored."""
        make_server(client, name="maint-node", status="MAINTENANCE")
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_online_server_is_eligible(self, client):
        """Rule 1: ONLINE server is selected."""
        make_server(client, status="ONLINE")
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201

    def test_mixed_statuses_only_online_used(self, client):
        """Rule 1: With OFFLINE + ONLINE servers, allocation uses ONLINE."""
        make_server(client, name="node-offline", status="OFFLINE")
        online = make_server(client, name="node-online", status="ONLINE").get_json()["server"]
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201
        assert r.get_json()["allocation"]["server_id"] == online["id"]

    def test_no_servers_at_all_returns_409(self, client):
        """Rule 1: No servers exist at all → 409."""
        w = make_workload(client).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409


# ====================================================================
# RULE 2 — CPU capacity
# ====================================================================

class TestRule2CpuCapacity:

    def test_cpu_exceeds_server_capacity_rejected(self, client):
        """Rule 2: workload CPU > server available CPU → reject."""
        make_server(client, cpu=4, ram=32768)
        w = make_workload(client, cpu=8, ram=1024).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_cpu_equals_available_accepted(self, client):
        """Rule 2: exact boundary — cpu_required == available_cpu → valid."""
        make_server(client, cpu=8, ram=32768)
        w = make_workload(client, cpu=8, ram=1024).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201

    def test_cpu_one_below_capacity_accepted(self, client):
        """Rule 2: cpu_required == capacity - 1 → valid."""
        make_server(client, cpu=8, ram=32768)
        w = make_workload(client, cpu=7, ram=1024).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201

    def test_cpu_one_above_available_rejected(self, client):
        """Rule 2: cpu_required == available_cpu + 1 → reject."""
        make_server(client, cpu=8, ram=32768)
        w = make_workload(client, cpu=9, ram=1024).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409


# ====================================================================
# RULE 3 — RAM capacity
# ====================================================================

class TestRule3RamCapacity:

    def test_ram_exceeds_server_capacity_rejected(self, client):
        """Rule 3: workload RAM > server available RAM → reject."""
        make_server(client, cpu=16, ram=1024)
        w = make_workload(client, cpu=1, ram=8192).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_ram_equals_available_accepted(self, client):
        """Rule 3: exact RAM boundary → valid."""
        make_server(client, cpu=16, ram=8192)
        w = make_workload(client, cpu=1, ram=8192).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201

    def test_ram_one_above_available_rejected(self, client):
        """Rule 3: ram_required == available_ram + 1 → reject."""
        make_server(client, cpu=16, ram=8192)
        w = make_workload(client, cpu=1, ram=8193).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409


# ====================================================================
# RULE 4 — Both CPU and RAM must be satisfied
# ====================================================================

class TestRule4BothResourcesMatter:

    def test_cpu_ok_ram_insufficient_rejected(self, client):
        """Rule 4: CPU fits but RAM doesn't → still rejected."""
        make_server(client, cpu=16, ram=1024)
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_ram_ok_cpu_insufficient_rejected(self, client):
        """Rule 4: RAM fits but CPU doesn't → still rejected."""
        make_server(client, cpu=2, ram=32768)
        w = make_workload(client, cpu=8, ram=1024).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_both_insufficient_rejected(self, client):
        """Rule 4: Neither CPU nor RAM fits → rejected."""
        make_server(client, cpu=1, ram=512)
        w = make_workload(client, cpu=8, ram=8192).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 409

    def test_both_exact_boundary_accepted(self, client):
        """Rule 4: Both CPU and RAM exactly at boundary → valid."""
        make_server(client, cpu=8, ram=16384)
        w = make_workload(client, cpu=8, ram=16384).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201


# ====================================================================
# RULE 5 — No partial allocation (resources unchanged on failure)
# ====================================================================

class TestRule5NoPartialAllocation:

    def test_failed_cpu_leaves_server_unchanged(self, client):
        """Rule 5: CPU rejection must NOT modify server resources."""
        s = make_server(client, cpu=2, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=8, ram=1024).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0

    def test_failed_ram_leaves_server_unchanged(self, client):
        """Rule 5: RAM rejection must NOT modify server resources."""
        s = make_server(client, cpu=16, ram=512).get_json()["server"]
        w = make_workload(client, cpu=1, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0

    def test_failed_allocation_leaves_workload_pending(self, client):
        """Rule 5: Workload status must remain PENDING after failed allocation."""
        make_server(client, cpu=1, ram=512)
        w = make_workload(client, cpu=8, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        wl = get_workload(client, w["id"])
        assert wl["status"] == "PENDING"

    def test_offline_rejection_leaves_resources_unchanged(self, client):
        """Rule 5: OFFLINE server rejection leaves zero resources."""
        s = make_server(client, status="OFFLINE").get_json()["server"]
        w = make_workload(client).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0


# ====================================================================
# RULE 6 — No duplicate allocation
# ====================================================================

class TestRule6NoDuplicateAllocation:

    def test_second_allocation_rejected(self, client):
        """Rule 6: Allocating the same workload twice → 409 on second."""
        make_server(client, cpu=32, ram=65536)
        w = make_workload(client).get_json()["workload"]
        r1 = allocate(client, w["id"])
        r2 = allocate(client, w["id"])
        assert r1.status_code == 201
        assert r2.status_code == 409

    def test_server_resources_not_double_charged(self, client):
        """Rule 6: Duplicate attempt must not change server resources."""
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])   # first — succeeds
        allocate(client, w["id"])   # second — must fail

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 4     # charged once only
        assert srv["allocated_ram"] == 8192


# ====================================================================
# RULE 7 — Best Fit deterministic selection
# ====================================================================

class TestRule7BestFitStrategy:

    def test_best_fit_selects_tightest_server(self, client):
        """
        Rule 7: Two servers — workload fits both, should go to tighter one.

          server-A: 16 CPU, 32768 MB  →  remaining after job: 12 + 24576 = 24588
          server-B:  8 CPU, 16384 MB  →  remaining after job:  4 + 8192  = 8196

        Best fit → server-B (lower score).
        """
        make_server(client, name="server-a", cpu=16, ram=32768)
        b = make_server(client, name="server-b", cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        r = allocate(client, w["id"])
        assert r.status_code == 201
        assert r.get_json()["allocation"]["server_id"] == b["id"]

    def test_only_eligible_server_chosen_when_one_is_full(self, client):
        """
        Rule 7 + Rule 2: server-A is full, server-B has room → server-B chosen.
        """
        # Fill server-A first
        sa = make_server(client, name="server-a", cpu=4, ram=8192).get_json()["server"]
        sb = make_server(client, name="server-b", cpu=16, ram=32768).get_json()["server"]

        fill_job = make_workload(client, name="fill-job", cpu=4, ram=8192).get_json()["workload"]
        allocate(client, fill_job["id"])  # goes to server-a (best fit)

        new_job = make_workload(client, name="new-job", cpu=4, ram=8192).get_json()["workload"]
        r = allocate(client, new_job["id"])
        assert r.status_code == 201
        assert r.get_json()["allocation"]["server_id"] == sb["id"]


# ====================================================================
# RULE 8 — Resource accounting
# ====================================================================

class TestRule8ResourceAccounting:

    def test_server_allocated_cpu_incremented(self, client):
        """Rule 8: server.allocated_cpu += workload.cpu_required."""
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 4

    def test_server_allocated_ram_incremented(self, client):
        """Rule 8: server.allocated_ram += workload.ram_required."""
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_ram"] == 8192

    def test_available_resources_decrease_after_allocation(self, client):
        """Rule 8: available_cpu and available_ram decrease correctly."""
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=6, ram=12288).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["available_cpu"] == 10
        assert srv["available_ram"] == 20480

    def test_multiple_allocations_accumulate_resources(self, client):
        """Rule 8: Two workloads allocated to same server → resources add up."""
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w1 = make_workload(client, name="job-1", cpu=4, ram=8192).get_json()["workload"]
        w2 = make_workload(client, name="job-2", cpu=6, ram=12288).get_json()["workload"]
        allocate(client, w1["id"])
        allocate(client, w2["id"])

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 10
        assert srv["allocated_ram"] == 20480

    def test_exact_capacity_allocation_leaves_zero_available(self, client):
        """Rule 8: Using all resources → available reaches zero."""
        s = make_server(client, cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=8, ram=16384).get_json()["workload"]
        allocate(client, w["id"])

        srv = get_server(client, s["id"])
        assert srv["available_cpu"] == 0
        assert srv["available_ram"] == 0


# ====================================================================
# RULE 9 — State consistency
# ====================================================================

class TestRule9Consistency:

    def test_workload_status_becomes_allocated(self, client):
        """Rule 9: Workload moves to ALLOCATED after success."""
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        assert get_workload(client, w["id"])["status"] == "PENDING"
        allocate(client, w["id"])
        assert get_workload(client, w["id"])["status"] == "ALLOCATED"

    def test_allocation_record_retrievable(self, client):
        """Rule 9: Allocation document persisted and retrievable by ID."""
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        alloc_id = allocate(client, w["id"]).get_json()["allocation"]["id"]

        r = client.get(f"/api/allocations/{alloc_id}")
        assert r.status_code == 200
        assert r.get_json()["allocation"]["id"] == alloc_id


# ====================================================================
# RULE 10 — Invalid request validation
# ====================================================================

class TestRule10InvalidRequests:

    def test_missing_workload_id_returns_400(self, client):
        """Rule 10: workload_id field absent → 400."""
        r = client.post("/api/allocations", json={})
        assert r.status_code == 400

    def test_empty_workload_id_returns_400(self, client):
        """Rule 10: workload_id is empty string → 400."""
        r = client.post("/api/allocations", json={"workload_id": ""})
        assert r.status_code == 400

    def test_nonexistent_workload_id_returns_404(self, client):
        """Rule 10: workload_id is valid format but no such workload → 404."""
        r = client.post("/api/allocations", json={"workload_id": "000000000000000000000000"})
        assert r.status_code == 404

    def test_invalid_id_format_returns_404(self, client):
        """Rule 10: malformed ObjectId → 404 (treated as not found)."""
        r = client.post("/api/allocations", json={"workload_id": "not-an-id"})
        assert r.status_code == 404

    def test_no_json_body_returns_400(self, client):
        """Rule 10: no JSON at all → 400."""
        r = client.post("/api/allocations", data="garbage")
        assert r.status_code == 400


# ====================================================================
# GET /api/allocations/<id>
# ====================================================================

class TestGetAllocation:

    def test_get_existing_allocation(self, client):
        make_server(client)
        w = make_workload(client).get_json()["workload"]
        alloc_id = allocate(client, w["id"]).get_json()["allocation"]["id"]
        r = client.get(f"/api/allocations/{alloc_id}")
        assert r.status_code == 200

    def test_get_nonexistent_allocation_returns_404(self, client):
        r = client.get("/api/allocations/000000000000000000000000")
        assert r.status_code == 404

    def test_get_invalid_id_returns_404(self, client):
        r = client.get("/api/allocations/bad-id")
        assert r.status_code == 404


# ====================================================================
# WORKLOAD EVICTION & RE-QUEUEING
# ====================================================================

class TestServerStatusChangeEvictsWorkloads:

    def test_evict_workloads_on_offline(self, client):
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        alloc = allocate(client, w["id"]).get_json()["allocation"]

        # Update status to OFFLINE
        r = client.patch(f"/api/servers/{s['id']}/status", json={"status": "OFFLINE"})
        assert r.status_code == 200

        # Check workload is back to PENDING
        wl = get_workload(client, w["id"])
        assert wl["status"] == "PENDING"

        # Check allocation record is gone
        alloc_r = client.get(f"/api/allocations/{alloc['id']}")
        assert alloc_r.status_code == 404

        # Check server resources are reset
        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0
        assert srv["status"] == "OFFLINE"

    def test_evict_workloads_on_maintenance(self, client):
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        alloc = allocate(client, w["id"]).get_json()["allocation"]

        # Update status to MAINTENANCE
        r = client.patch(f"/api/servers/{s['id']}/status", json={"status": "MAINTENANCE"})
        assert r.status_code == 200

        # Check workload is back to PENDING
        wl = get_workload(client, w["id"])
        assert wl["status"] == "PENDING"

        # Check allocation record is gone
        alloc_r = client.get(f"/api/allocations/{alloc['id']}")
        assert alloc_r.status_code == 404

        # Check server resources are reset
        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 0
        assert srv["allocated_ram"] == 0
        assert srv["status"] == "MAINTENANCE"

    def test_no_eviction_on_online(self, client):
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        alloc = allocate(client, w["id"]).get_json()["allocation"]

        # Update status to ONLINE (no change)
        r = client.patch(f"/api/servers/{s['id']}/status", json={"status": "ONLINE"})
        assert r.status_code == 200

        # Workload should remain ALLOCATED
        wl = get_workload(client, w["id"])
        assert wl["status"] == "ALLOCATED"

        # Allocation record exists
        alloc_r = client.get(f"/api/allocations/{alloc['id']}")
        assert alloc_r.status_code == 200

        # Resources remain allocated
        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 4
        assert srv["allocated_ram"] == 8192


class TestServerDeletionEvictsWorkloads:

    def test_evict_workloads_on_deletion(self, client):
        s = make_server(client, cpu=16, ram=32768).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        alloc = allocate(client, w["id"]).get_json()["allocation"]

        # Delete server
        r = client.delete(f"/api/servers/{s['id']}")
        assert r.status_code == 200

        # Check workload is back to PENDING
        wl = get_workload(client, w["id"])
        assert wl["status"] == "PENDING"

        # Check allocation record is gone
        alloc_r = client.get(f"/api/allocations/{alloc['id']}")
        assert alloc_r.status_code == 404


class TestWorkloadDeletionFreesResources:
    def test_delete_allocated_workload_frees_server_resources(self, client):
        s = make_server(client, cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        alloc = allocate(client, w["id"]).get_json()["allocation"]

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 4
        assert srv["allocated_ram"] == 8192

        r = client.delete(f"/api/workloads/{w['id']}")
        assert r.status_code == 200

        srv_after = get_server(client, s["id"])
        assert srv_after["allocated_cpu"] == 0
        assert srv_after["allocated_ram"] == 0

        alloc_r = client.get(f"/api/allocations/{alloc['id']}")
        assert alloc_r.status_code == 404


class TestModifyAllocatedWorkloadResources:
    def test_modify_resources_success_within_capacity(self, client):
        s = make_server(client, cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        r = client.patch(f"/api/workloads/{w['id']}", json={"cpu_required": 6, "ram_required": 12288})
        assert r.status_code == 200

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 6
        assert srv["allocated_ram"] == 12288

    def test_modify_resources_fails_exceeding_capacity(self, client):
        s = make_server(client, cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        r = client.patch(f"/api/workloads/{w['id']}", json={"cpu_required": 10, "ram_required": 8192})
        assert r.status_code == 409

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 4
        assert srv["allocated_ram"] == 8192

    def test_modify_resources_same_or_smaller_value_success(self, client):
        s = make_server(client, cpu=8, ram=16384).get_json()["server"]
        w = make_workload(client, cpu=4, ram=8192).get_json()["workload"]
        allocate(client, w["id"])

        r = client.patch(f"/api/workloads/{w['id']}", json={"cpu_required": 2, "ram_required": 4096})
        assert r.status_code == 200

        srv = get_server(client, s["id"])
        assert srv["allocated_cpu"] == 2
        assert srv["allocated_ram"] == 4096

