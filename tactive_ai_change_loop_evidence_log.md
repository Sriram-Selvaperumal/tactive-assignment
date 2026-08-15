# AI Change-Loop Evidence Log
### DataCentre Allocator — Agentic Development Record
**Project:** Tactive SDLC Assessment  
**Repository:** `Sriram-Selvaperumal/tactive-assignment`  
**Stack:** Flask · MongoDB Atlas · Vanilla HTML/CSS/JS · Pytest  
**Total Versions Shipped:** V1.1 → V1.2 → V1.3  
**Total Automated Tests:** 103 (all passing on final run)

---

> This document is a complete, chronological record of every engineering prompt, architectural decision, code change, test failure, correction, and verification made during the AI-assisted development of the DataCentre Allocator project. It captures the full Red-Green-Refactor discipline applied across all three development iterations.

---

## Table of Contents

1. [Project Architecture Decision](#1-project-architecture-decision)
2. [V1.1 — Base Initialization](#2-v11--base-initialization)
3. [MongoDB Connection Setup](#3-mongodb-connection-setup)
4. [Testing Strategy & Baseline Test Run](#4-testing-strategy--baseline-test-run)
5. [V1.2 — Server Status & Workload Management](#5-v12--server-status--workload-management)
6. [V1.3 — Workload Management Enhancements](#6-v13--workload-management-enhancements)
7. [Repository Restructure](#7-repository-restructure)
8. [Red-Green-Refactor Cycle](#8-red-green-refactor-cycle)
9. [Final Verification](#9-final-verification)

---

## 1. Project Architecture Decision

### Engineering Prompt
> *"Initialize version 1.1 of the DataCentre Allocator — a server resource management system. The backend should be built with Flask (Python), the database layer with MongoDB, and the frontend as a minimal single-page application using plain HTML, CSS, and JavaScript.*
>
> *Architectural requirements: adopt a strict layered separation of concerns — routes must not contain business logic, business logic must not contain database queries, and database queries must not contain domain validation. Prioritize building a clean, testable backend foundation. Ship only the core MVP scope — server registration, workload registration, and workload-to-server allocation. Do not pre-implement features planned for later versions."*

### Engineering Decision

Before writing a single line of code, the architecture was designed with long-term extensibility in mind. The key decision was to adopt a **strict layered architecture** — a deliberate choice to prevent logic from leaking between concerns and to make testing possible without mocking.

```
┌─────────────────────────────────────────────────────────┐
│                      HTTP Layer                          │
│          Flask Blueprints  (app/routes/)                 │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│       AllocationService  (app/services/)                 │
│   Business rules, orchestration, domain validation       │
├─────────────────────────────────────────────────────────┤
│                  Repository Layer                        │
│  ServerRepository · WorkloadRepository · AllocRepo       │
│      Pure MongoDB CRUD — no business logic here          │
├─────────────────────────────────────────────────────────┤
│                    Domain Models                         │
│     Server · Workload · Allocation  (app/models/)        │
│           Typed dataclasses, no DB coupling              │
├─────────────────────────────────────────────────────────┤
│                    Database Layer                        │
│         MongoClient singleton  (app/database/)           │
│      Config-aware: Dev / Test / Prod  (app/config.py)    │
└─────────────────────────────────────────────────────────┘
```

**Why this matters:** The Repository pattern allows the test suite to swap in a dedicated `datacenter_test_db` database per test with zero mocking — full integration confidence from day one.

---

## 2. V1.1 — Base Initialization

### Files Created

| File | Purpose |
|---|---|
| `app/__init__.py` | Application factory `create_app()` |
| `app/config.py` | DevelopmentConfig / TestingConfig / ProductionConfig |
| `app/database/__init__.py` | MongoDB singleton connection |
| `app/errors.py` | Centralized error handlers (404, 400, 500) |
| `app/models/server.py` | `Server` dataclass — name, cpu_total, ram_total, status |
| `app/models/workload.py` | `Workload` dataclass — name, cpu_required, ram_required, status |
| `app/models/allocation.py` | `Allocation` dataclass — workload_id, server_id, timestamps |
| `app/repositories/server_repository.py` | CRUD for servers |
| `app/repositories/workload_repository.py` | CRUD for workloads |
| `app/repositories/allocation_repository.py` | CRUD for allocations |
| `app/services/allocation_service.py` | Core allocation business rules |
| `app/validators/request_validators.py` | Input validation helpers |
| `app/routes/servers.py` | Server API blueprint |
| `app/routes/workloads.py` | Workload API blueprint |
| `app/routes/allocations.py` | Allocation API blueprint |
| `app/routes/health.py` | Health check endpoint |
| `static/css/style.css` | Minimal, clean frontend stylesheet |
| `static/js/app.js` | Vanilla JS SPA — fetch API calls and DOM rendering |
| `templates/index.html` | Single-page application shell |
| `run.py` | Application entrypoint |

### Allocation Business Rules Implemented (V1.1)

| Rule | Description |
|---|---|
| Rule 1 | Only `ONLINE` servers are eligible for allocation |
| Rule 2 | Server must have sufficient available CPU |
| Rule 3 | Server must have sufficient available RAM |
| Rule 4 | Both CPU *and* RAM must pass — either alone is insufficient |
| Rule 5 | No partial allocation — if ineligible, nothing changes |
| Rule 6 | No duplicate allocation — a workload cannot be allocated twice |
| Rule 7 | Best-fit strategy — select the server with the least remaining slack |
| Rule 8 | Resource accounting — `allocated_cpu` and `allocated_ram` are updated on server |
| Rule 9 | Consistency — workload status transitions to `ALLOCATED` |
| Rule 10 | Invalid requests rejected with `400 Bad Request` or `404 Not Found` |

---

## 3. MongoDB Connection Setup

### Engineering Prompt
> *"Provide step-by-step instructions to provision a MongoDB Atlas cluster, create a database user with the appropriate roles, configure network access, and retrieve the connection string for integration with the Flask application. Include instructions for running the application locally after the environment is configured."*

### Process
1. Created a MongoDB Atlas account and provisioned the `tactive` shared cluster
2. Configured IP network access allowlist
3. Created a database user with `readWrite` role scoped to `datacenter_db`
4. Retrieved the SRV connection string from Atlas UI
5. Populated `.env` from `.env.example` template

### Final Resolved URI (written to `.env`)
```
MONGO_URI=mongodb+srv://tactive:****@tactive.2smo6qd.mongodb.net/?retryWrites=true&w=majority&appName=tactive
DATABASE_NAME=datacenter_db
```

> **Note:** `.env` is gitignored. The `.env.example` template is committed to the repository for reproducibility without exposing secrets.

---

## 4. Testing Strategy & Baseline Test Run

### Engineering Prompt
> *"Design and generate a comprehensive automated test suite for the V1.1 application. Tests should target edge cases, boundary conditions, and invalid input handling across all endpoints. The test evidence — including terminal output logs and failure screenshots — should be captured and preserved as documentation artefacts for the baseline release."*

### Test Design Philosophy

Tests were written as **black-box integration tests** — interacting only through the HTTP API layer, exactly as a real client would. This validates the full stack (routes → service → repository → MongoDB) in a single pass with no mocking.

Each test class maps directly to a specific business rule:

```
tests/
├── conftest.py                   — Pytest fixtures, test app factory, DB teardown
├── test_servers.py               — Server CRUD and status management
├── test_workloads.py             — Workload creation, listing, resource validation
└── test_allocations.py           — All 10 allocation business rules + eviction logic
    ├── TestRule1OnlineOnly
    ├── TestRule2CpuSufficiency
    ├── TestRule3RamSufficiency
    ├── TestRule4BothResourcesMatter
    ├── TestRule5NoPartialAllocation
    ├── TestRule6NoDuplicateAllocation
    ├── TestRule7BestFitStrategy
    ├── TestRule8ResourceAccounting
    ├── TestRule9Consistency
    ├── TestRule10InvalidRequests
    ├── TestGetAllocation
    ├── TestServerStatusChangeEvictsWorkloads
    ├── TestServerDeletionEvictsWorkloads
    ├── TestWorkloadDeletionFreesResources
    └── TestModifyAllocatedWorkloadResources
```

### Baseline Test Evidence
Test logs and screenshots are stored under:
```
tactive_test_logs/
├── 1_test_scripts/               — Copies of test scripts at baseline
└── 2_baseline_test/
    ├── baseline_test_logs.txt    — Full terminal output
    └── screenshots/              — Evidence screenshots
        ├── image.png
        ├── img2.png
        └── img3.png
```

---

## 5. V1.2 — Server Status & Workload Management

### Engineering Prompt
> *"Implement a Server Status and Workload Eviction system with the following specifications:*
>
> **(1) Server Status Transitions:** Expose a PATCH endpoint that allows transitioning a server's operational status between Online, Offline, and Maintenance. The UI should reflect the current status with clear visual indicators and provide an action control to initiate transitions.*
>
> **(2) Server Deletion:** Expose a DELETE endpoint for permanent server removal. Require an explicit confirmation step at the UI layer before the request is issued. The server must be removed from all active views upon deletion.*
>
> **(3) Workload Eviction Policy:** When a server transitions to Offline or Maintenance, or is deleted, all workloads currently allocated to that server must be automatically re-queued. The eviction process should: identify all affected allocations, reset workload statuses to PENDING, remove allocation records, and reset the server's resource utilization counters.*
>
> *Scope is strictly limited to these three features. Do not introduce changes outside this scope."*

### Implementation Plan

Before implementation, all state transitions and their side-effects were mapped:

- **API Changes:** `PATCH /api/servers/<id>` for status update, `DELETE /api/servers/<id>` for deletion
- **Eviction Logic:** Status change to Offline/Maintenance/Deleted → find all `ALLOCATED` workloads on that server → set them back to `PENDING` → delete allocation records → reset server resource counters
- **UI Changes:** Status badge with colour coding, action buttons on server cards, confirmation step before deletion
- **Test Coverage:** New test classes for status eviction and server deletion eviction

### Key Engineering Decision — Compensating Transactions

MongoDB Atlas free-tier clusters do not guarantee multi-document atomic transactions without replica set configuration. Rather than introducing infrastructure complexity, a **compensating operations pattern** was adopted in the service layer:

```python
# Eviction sequence — compensating at implementation, atomic at intent
1. Find all allocations for the server  →  allocation_repository.get_by_server_id()
2. Reset workload statuses to PENDING   →  workload_repository.update_status()
3. Delete allocation records            →  allocation_repository.delete()
4. Reset server resource counters       →  server_repository.reset_resources()
5. Apply status change to server        →  server_repository.update_status()
```

This ensures that even in partial failure scenarios, the system trends towards consistency — workloads are re-queued rather than stranded in an `ALLOCATED` state with no valid server.

### Files Modified (V1.2)

| File | Change |
|---|---|
| `app/repositories/server_repository.py` | Added `update_status`, `delete`, `reset_resources` methods |
| `app/repositories/allocation_repository.py` | Added `get_by_server_id`, `delete_by_server_id` methods |
| `app/services/allocation_service.py` | Added `update_server_status`, `delete_server` with eviction logic |
| `app/routes/servers.py` | Added `PATCH` and `DELETE` endpoint handlers |
| `static/js/app.js` | Added status toggle buttons, delete with confirmation, UI state updates |
| `templates/index.html` | Added status badges, action controls on server cards |
| `tests/test_servers.py` | Added `TestUpdateServerStatus`, `TestDeleteServer` |
| `tests/test_allocations.py` | Added `TestServerStatusChangeEvictsWorkloads`, `TestServerDeletionEvictsWorkloads` |

### Test Results (V1.2)
```
======================= 93 passed in 98.24s (0:01:38) =======================
```

---

## 6. V1.3 — Workload Management Enhancements

### Engineering Prompt
> *"Extend the Workload Management subsystem with the following capabilities:*
>
> **(1) Workload Deletion:** Implement a DELETE endpoint for permanent workload removal. The operation must be idempotent for non-existent resources. If the workload is in ALLOCATED state, the deletion must atomically release the associated CPU and RAM from the server and remove the allocation record before deleting the workload document. No orphaned allocation records should remain after deletion.*
>
> **(2) Resource Modification:** Implement a PATCH endpoint to update the cpu_required and ram_required fields of an existing workload. Validation rules: for PENDING workloads, update the document directly. For ALLOCATED workloads, validate that the new resource request does not exceed the server's available headroom — critically, the workload's own existing allocation must not count against it during this validation. Apply the resource delta (new − old) to the server's utilization counters. Reject requests exceeding capacity with HTTP 409 Conflict and leave all data unchanged.*
>
> **(3) UI Controls:** Add Edit and Delete actions to each workload card. Require confirmation before deletion. Resource modification should be presented inline.*
>
> *Scope is strictly limited to these enhancements. Do not modify existing allocation, server, or unrelated workload logic."*

### Implementation Plan

Before implementation, all state × action combinations were modelled:

```
WORKLOAD STATE × ACTION MATRIX

┌──────────────┬───────────────────────────┬───────────────────────────────────┐
│ State        │ Delete                    │ Modify Resources                  │
├──────────────┼───────────────────────────┼───────────────────────────────────┤
│ PENDING      │ Delete document only      │ Update workload document directly │
│ ALLOCATED    │ Release server resources  │ Validate server headroom;         │
│              │ → Delete allocation       │ apply delta (new − old) to server │
│              │ → Delete workload         │ counters; reject with 409 if over │
└──────────────┴───────────────────────────┴───────────────────────────────────┘
```

### Capacity Check Logic for Modify (Allocated Workloads)

A subtle but critical correctness concern: when validating a resource modification for an already-allocated workload, the workload's existing footprint must not count against itself.

```python
# INCORRECT — workload's own allocation is already subtracted from available_cpu:
if server.available_cpu < new_cpu:
    raise InsufficientResourcesError()

# CORRECT — restore the workload's current footprint to compute true headroom:
max_available_cpu = server.available_cpu + workload.cpu_required
if max_available_cpu < new_cpu:
    raise InsufficientResourcesError()

# Apply the signed delta to the server:
cpu_delta = new_cpu - workload.cpu_required   # positive = uses more, negative = frees
server_repository.increment_resources(server_id, cpu_delta, ram_delta)
```

### Files Modified (V1.3)

| File | Change |
|---|---|
| `app/repositories/workload_repository.py` | Added `delete`, `update_resources` methods |
| `app/services/allocation_service.py` | Added `delete_workload`, `update_workload_resources` with delta accounting |
| `app/routes/workloads.py` | Added `DELETE /api/workloads/<id>` and `PATCH /api/workloads/<id>` |
| `static/js/app.js` | Added Edit/Delete buttons with confirmation dialogs on workload cards |
| `tests/test_workloads.py` | Added `TestUpdateWorkloadResources`, `TestDeleteWorkload` |
| `tests/test_allocations.py` | Added `TestWorkloadDeletionFreesResources`, `TestModifyAllocatedWorkloadResources` |

### New Test Classes Added (V1.3)

| Test Class | Scenarios Covered |
|---|---|
| `TestUpdateWorkloadResources` | Valid update, invalid values, missing fields, nonexistent workload |
| `TestDeleteWorkload` | Delete existing workload, delete nonexistent workload |
| `TestWorkloadDeletionFreesResources` | Allocated workload deletion releases CPU/RAM, removes allocation record |
| `TestModifyAllocatedWorkloadResources` | Modify within capacity ✓, modify exceeding capacity → 409 ✗, reduce to smaller value ✓ |

### Test Results (V1.3)
```
======================= 103 passed in 115.14s (0:01:55) =======================
```

---

## 7. Repository Restructure

### Engineering Prompt
> *"The local workspace has been reorganized — the Flask application now resides under a tactive_project/ subdirectory and test evidence assets are stored alongside it in tactive_test_logs/. The Git repository control directory is currently misaligned with this new layout. Reconcile the repository root with the new folder structure and push the updated tree to origin, ensuring that all file moves are tracked as renames to preserve commit history continuity."*

### Problem Encountered
After the filesystem reorganization, the `.git` directory remained inside `tactive_project/`. The new root contained both `tactive_project/` and `tactive_test_logs/` as siblings, which meant:
- Running `git status` from the root → `fatal: not a git repository`
- `tactive_test_logs/` was entirely invisible to git (it existed outside the repo root)

### Resolution

```powershell
# 1. Relocate the Git control directory to the true workspace root
move tactive_project\.git .git

# 2. Relocate .gitignore to cover the full directory tree
move tactive_project\.gitignore .gitignore

# 3. Stage all changes — git detects renames automatically via similarity index
git add -A

# 4. Commit — all 34 moved files are recorded as renames, not delete+create
git commit -m "Restructure project layout and add test logs and screenshots"

git push
```

### Final Folder Structure (Post-Restructure)

```
Tactive/
├── tactive_project/              ← Flask application
│   ├── app/
│   ├── static/
│   ├── templates/
│   ├── tests/
│   ├── run.py
│   ├── requirements.txt
│   └── pytest.ini
└── tactive_test_logs/            ← Test evidence (now tracked by git)
    ├── 1_test_scripts/           ← Test scripts archived at baseline
    └── 2_baseline_test/
        ├── baseline_test_logs.txt
        └── screenshots/
```

**Git correctly identified all 34 file moves as renames — full commit history preserved.**

---

## 8. Red-Green-Refactor Cycle

### Engineering Prompt (Break)
> *"Introduce deliberate logic regressions into the allocation service to produce a failing test run. The regressions should target specific business rules so that the test suite's ability to catch them can be demonstrated. Select bugs that are subtle enough to be realistic but specific enough that the failing test names clearly identify the violated rule."*

### Bugs Introduced

#### Bug 1 — Off-by-One Boundary Condition (Rule 4 / Rule 8)
**File:** `app/services/allocation_service.py`

```diff
 eligible = [
     s for s in online_servers
-    if s.available_cpu >= workload.cpu_required    # CORRECT — exact match allowed
+    if s.available_cpu > workload.cpu_required     # BROKEN — rejects exact match
     and s.available_ram >= workload.ram_required
 ]
```

**Tests Expected to Fail:**
- `TestRule4BothResourcesMatter::test_both_exact_boundary_accepted`
- `TestRule8ResourceAccounting::test_exact_capacity_allocation_leaves_zero_available`

#### Bug 2 — Disabled Duplicate Allocation Guard (Rule 6)
**File:** `app/services/allocation_service.py`

```diff
-if workload.status == WorkloadStatus.ALLOCATED:
-    raise WorkloadAlreadyAllocatedError(...)
+# Guard commented out — allows double-allocation of the same workload
```

**Tests Expected to Fail:**
- `TestRule6NoDuplicateAllocation::test_second_allocation_rejected`
- `TestRule6NoDuplicateAllocation::test_server_resources_not_double_charged`

### Outcome
Running the test suite with regressions in place produced the expected RED failures, confirming that the test coverage correctly identified both violated rules.

---

### Engineering Prompt (Fix)
> *"The regression cycle is complete. Restore the allocation service to its correct implementation. Both the boundary condition operator and the duplicate allocation guard must be reverted to their original state before the final test run is executed."*

### Corrections Applied

```diff
# Fix 1 — Restore boundary condition operator
-    if s.available_cpu > workload.cpu_required
+    if s.available_cpu >= workload.cpu_required

# Fix 2 — Restore Rule 6 duplicate allocation guard
-        # Guard commented out
+        if workload.status == WorkloadStatus.ALLOCATED:
+            raise WorkloadAlreadyAllocatedError(
+                f"Workload '{workload.name}' is already allocated."
+            )
```

---

## 9. Final Verification

### Command
```powershell
cd c:\Users\srira\OneDrive\Desktop\Tactive\tactive_project
venv\Scripts\python.exe -m pytest tests/ -v
```

### Final Test Results

```
tests/test_allocations.py::TestRule1OnlineOnly::...                         PASSED
tests/test_allocations.py::TestRule2CpuSufficiency::...                     PASSED
tests/test_allocations.py::TestRule3RamSufficiency::...                     PASSED
tests/test_allocations.py::TestRule4BothResourcesMatter::...                PASSED
tests/test_allocations.py::TestRule5NoPartialAllocation::...                PASSED
tests/test_allocations.py::TestRule6NoDuplicateAllocation::...              PASSED
tests/test_allocations.py::TestRule7BestFitStrategy::...                    PASSED
tests/test_allocations.py::TestRule8ResourceAccounting::...                 PASSED
tests/test_allocations.py::TestRule9Consistency::...                        PASSED
tests/test_allocations.py::TestRule10InvalidRequests::...                   PASSED
tests/test_allocations.py::TestGetAllocation::...                           PASSED
tests/test_allocations.py::TestServerStatusChangeEvictsWorkloads::...       PASSED
tests/test_allocations.py::TestServerDeletionEvictsWorkloads::...           PASSED
tests/test_allocations.py::TestWorkloadDeletionFreesResources::...          PASSED
tests/test_allocations.py::TestModifyAllocatedWorkloadResources::...        PASSED
tests/test_servers.py::TestCreateServer::...                                PASSED
tests/test_servers.py::TestListServers::...                                 PASSED
tests/test_servers.py::TestGetServer::...                                   PASSED
tests/test_servers.py::TestUpdateServerStatus::...                          PASSED
tests/test_servers.py::TestDeleteServer::...                                PASSED
tests/test_workloads.py::TestCreateWorkload::...                            PASSED
tests/test_workloads.py::TestListWorkloads::...                             PASSED
tests/test_workloads.py::TestGetWorkload::...                               PASSED
tests/test_workloads.py::TestUpdateWorkloadResources::...                   PASSED
tests/test_workloads.py::TestDeleteWorkload::...                            PASSED

======================= 103 passed in 115.14s (0:01:55) =======================
```

### Version Summary

| Version | Feature Scope | Tests | Status |
|---|---|---|---|
| V1.1 | Base application — servers, workloads, allocations, best-fit engine | 58 | ✅ All green |
| V1.2 | Server status management, server deletion, workload eviction | 93 | ✅ All green |
| V1.3 | Workload delete, workload resource modification with delta accounting | 103 | ✅ All green |

---

*Document generated: 2026-08-15*  
*Repository: [github.com/Sriram-Selvaperumal/tactive-assignment](https://github.com/Sriram-Selvaperumal/tactive-assignment)*
