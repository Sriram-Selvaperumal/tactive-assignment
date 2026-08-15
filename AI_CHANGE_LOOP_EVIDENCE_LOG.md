# AI Change-Loop Evidence Log
### DataCentre Allocator — Agentic Development Record
**Project:** Tactive SDLC Assessment  
**Repository:** `Sriram-Selvaperumal/tactive-assignment`  
**Stack:** Flask · MongoDB Atlas · Vanilla HTML/CSS/JS · Pytest  
**Total Versions Shipped:** V1.1 → V1.2 → V1.3  
**Total Automated Tests:** 103 (all passing on final run)

---

> This document is a complete, chronological record of every prompt, decision, change, failure, correction, and verification made during the AI-assisted development of the DataCentre Allocator project. It captures the engineering discipline applied across all three development iterations.

---

## Table of Contents

1. [Project Architecture Decision](#1-project-architecture-decision)
2. [V1.1 — Base Initialization](#2-v11--base-initialization)
3. [MongoDB Connection Setup](#3-mongodb-connection-setup)
4. [Testing Strategy & Baseline Test Run](#4-testing-strategy--baseline-test-run)
5. [V1.2 — Server Status & Workload Management](#5-v12--server-status--workload-management)
6. [V1.3 — Workload Management Enhancements](#6-v13--workload-management-enhancements)
7. [Repository Restructure](#7-repository-restructure)
8. [Red-Green-Refactor Cycle (Deliberate Break & Fix)](#8-red-green-refactor-cycle-deliberate-break--fix)
9. [Final Verification](#9-final-verification)

---

## 1. Project Architecture Decision

### Prompt
> *"Initialise the base web application — version 1.1. Backend: Flask Python. Frontend: HTML + CSS + JS. DB: MongoDB. Keep the frontend simple, clean, minimal, easy to understand. Focus on building clean backend architecture in order to ship a very first version."*
>
> **Negative Prompt:** *"Referring to the full implementation plan and building the entire version rather than the basic first version."*

### Engineering Decision

Before writing a single line of code, the architecture was designed with long-term extensibility in mind. The key decision was to adopt a **strict layered architecture** — a deliberate choice to prevent logic from leaking between concerns and to make testing possible without a live database.

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

**Why this matters:** The Repository pattern means the test suite could swap in a clean `datacenter_test_db` database per test — no mocking, no fixtures with fake data, full integration confidence.

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
| Rule 4 | Both CPU *and* RAM must pass — either alone is not enough |
| Rule 5 | No partial allocation — if ineligible, nothing changes |
| Rule 6 | No duplicate allocation — a workload cannot be allocated twice |
| Rule 7 | Best-fit strategy — select the server with the least remaining slack |
| Rule 8 | Resource accounting — `allocated_cpu` and `allocated_ram` are updated on server |
| Rule 9 | Consistency — workload status transitions to `ALLOCATED` |
| Rule 10 | Invalid requests rejected with `400 Bad Request` or `404 Not Found` |

---

## 3. MongoDB Connection Setup

### Prompt
> *"Since you need MongoDB connection string, tell me how to get it and say how to run the project."*

### Process
The agent walked the user through:
1. Creating a MongoDB Atlas account
2. Creating the `tactive` cluster
3. Configuring network access (IP allowlist)
4. Creating a database user with credentials
5. Copying the connection string from Atlas UI

### Connection String Provided by User
```
mongodb+srv://tactive:<db_password>@tactive.2smo6qd.mongodb.net/?appName=tactive
```

### Final Resolved URI (written to `.env`)
```
MONGO_URI=mongodb+srv://tactive:tactiveuser123@tactive.2smo6qd.mongodb.net/?retryWrites=true&w=majority&appName=tactive
DATABASE_NAME=datacenter_db
```

> **Note:** `.env` is gitignored. The `.env.example` template is committed to the repository for reproducibility without exposing secrets.

---

## 4. Testing Strategy & Baseline Test Run

### Prompt
> *"I need AI-generated test scripts that test edge cases. I need screenshots of failing test cases to add in the documentation."*

### Test Design Philosophy

Tests were written as **black-box integration tests** — they interact only through the HTTP API layer, just like a real client. This validates the full stack (routes → service → repository → MongoDB) in one pass.

Each test class maps to a specific business rule:

```
tests/
├── conftest.py                   — Pytest fixtures, test app factory, DB cleanup
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

### Baseline Test Log
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

### Prompt
> *"Implement a comprehensive Server Status & Workload Management feature.*
>
> **Server Status Management:** Allow users to update status — Online, Offline, Maintenance. Status changes should be reflected immediately across the application.*
>
> **Delete Server:** Add an option to permanently delete a server. Require a confirmation step before deletion.*
>
> **Workload Management:** When a server is moved to Offline, Maintenance, or Deleted, automatically move affected tasks to a pending queue."*

### Implementation Plan

The agent created a formal implementation plan before touching any code:

- **API Changes:** `PATCH /api/servers/<id>` for status update, `DELETE /api/servers/<id>` for deletion
- **Eviction Logic:** When a server goes Offline/Maintenance/Deleted → find all `ALLOCATED` workloads on that server → set them back to `PENDING` → delete allocation records → reset server resource counters
- **UI Changes:** Status badge with color coding, action buttons on server cards, confirmation modal before deletion
- **Test Coverage:** New test classes for status eviction and server deletion eviction

### Key Engineering Decisions

**Compensating Transactions over MongoDB Transactions**

MongoDB Atlas free-tier clusters do not support multi-document transactions by default. Rather than introducing complexity around replica set configurations, a **compensating operations pattern** was adopted in the service layer:

```python
# Eviction sequence (atomic at intent, compensating at implementation)
1. Find all allocations for the server  →  allocation_repository.get_by_server_id()
2. Reset workload statuses to PENDING   →  workload_repository.update_status()
3. Delete allocation records            →  allocation_repository.delete()
4. Reset server resource counters       →  server_repository.reset_resources()
5. Apply status change to server        →  server_repository.update_status()
```

This ensures that even in the event of a partial failure, the system trends towards consistency (workloads are re-queued, not stranded).

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

### Prompt
> *"Implement the following enhancements to the Workload Management functionality:*
>
> **1. Delete Workload:** Allow authorized users to permanently delete a workload. Add confirmation dialog. Ensure deletion removes the workload from all relevant lists and releases server resources if allocated.*
>
> **2. Modify CPU Cores & RAM:** Allow users to modify CPU and RAM allocation of an existing workload. Validate that requested allocation does not exceed available resources of the assigned server."*

### Implementation Plan

Before implementation, the agent mapped out all edge cases and state transitions:

```
WORKLOAD STATE × ACTION MATRIX

┌──────────────┬───────────────────────────┬───────────────────────────────────┐
│ State        │ Delete                    │ Modify Resources                  │
├──────────────┼───────────────────────────┼───────────────────────────────────┤
│ PENDING      │ Delete document           │ Update workload document directly │
│ ALLOCATED    │ Release server resources  │ Validate server has overhead;     │
│              │ → Delete allocation       │ adjust server utilization by Δ    │
│              │ → Delete workload         │ (new_resource - old_resource)     │
└──────────────┴───────────────────────────┴───────────────────────────────────┘
```

### Capacity Check Logic for Modify (Allocated Workloads)

A subtle but critical correctness concern: when modifying an allocated workload's resource request, the workload's *own* existing allocation must not count against it during validation.

```python
# WRONG — counts the workload's own allocation against it:
if server.available_cpu < new_cpu:  # available_cpu is already reduced by this workload
    raise InsufficientResourcesError()

# CORRECT — temporarily restore the workload's current allocation to get true headroom:
max_available_cpu = server.available_cpu + workload.cpu_required
if max_available_cpu < new_cpu:
    raise InsufficientResourcesError()

# Then apply the delta:
cpu_delta = new_cpu - workload.cpu_required  # +ve = uses more, -ve = frees
server_repository.increment_resources(server_id, cpu_delta, ram_delta)
```

### Files Modified (V1.3)

| File | Change |
|---|---|
| `app/repositories/workload_repository.py` | Added `delete`, `update_resources` methods |
| `app/services/allocation_service.py` | Added `delete_workload`, `update_workload_resources` with delta accounting |
| `app/routes/workloads.py` | Added `DELETE /api/workloads/<id>` and `PATCH /api/workloads/<id>` |
| `static/js/app.js` | Added Edit/Delete buttons with confirmation prompts on workload cards |
| `tests/test_workloads.py` | Added `TestUpdateWorkloadResources`, `TestDeleteWorkload` |
| `tests/test_allocations.py` | Added `TestWorkloadDeletionFreesResources`, `TestModifyAllocatedWorkloadResources` |

### New Test Classes Added (V1.3)

| Test Class | Scenarios Covered |
|---|---|
| `TestUpdateWorkloadResources` | Valid update, invalid values, missing fields, nonexistent workload |
| `TestDeleteWorkload` | Delete existing, delete nonexistent |
| `TestWorkloadDeletionFreesResources` | Deleting allocated workload releases CPU/RAM, removes allocation record |
| `TestModifyAllocatedWorkloadResources` | Modify within capacity ✓, modify exceeding capacity ✗, reduce to smaller value ✓ |

### Test Results (V1.3)
```
======================= 103 passed in 115.14s (0:01:55) =======================
```

---

## 7. Repository Restructure

### Prompt
> *"Bro I changed folder structure a little bit, can you push it to GitHub?"*

### Problem Encountered
After the user reorganized the filesystem, the `.git` directory was still inside `tactive_project/` but the new root structure had both `tactive_project/` and `tactive_test_logs/` as siblings. This meant:
- `git status` from root → `fatal: not a git repository`
- `tactive_test_logs/` was invisible to git (outside the repo root)

### Resolution

```powershell
# Move .git control directory to the new root
move tactive_project\.git .git

# Move .gitignore to cover the full tree
move tactive_project\.gitignore .gitignore

# Stage all renames and new files
git add -A

# Commit — git correctly detected renames (100% similarity) instead of delete+add
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

**Git correctly identified all 34 file moves as renames (not deletes/creates) — full history preserved.**

---

## 8. Red-Green-Refactor Cycle (Deliberate Break & Fix)

### Prompt (Break)
> *"Break the application deliberately to make a red test."*

### Intent
Demonstrate the value of the test suite: intentionally introduce logic bugs and observe the test harness catch them.

### Bugs Introduced

#### Bug 1 — Off-by-One Boundary Condition
**File:** `app/services/allocation_service.py`

```diff
 eligible = [
     s for s in online_servers
-    if s.available_cpu >= workload.cpu_required    # CORRECT
+    if s.available_cpu > workload.cpu_required     # BROKEN — excludes exact match
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
+# DISABLED — allows double-allocation of the same workload
```

**Tests Expected to Fail:**
- `TestRule6NoDuplicateAllocation::test_second_allocation_rejected`
- `TestRule6NoDuplicateAllocation::test_server_resources_not_double_charged`

### Test Run with Broken Code
Running `venv\Scripts\python.exe -m pytest tests/ -v` produced **RED failures** confirming the test suite caught both bugs precisely as designed.

---

### Prompt (Fix)
> *"Now fix the broken parts — I am going to run the final test."*

### Corrections Applied

```diff
# Fix 1 — Restore boundary condition
-    if s.available_cpu > workload.cpu_required
+    if s.available_cpu >= workload.cpu_required

# Fix 2 — Restore Rule 6 duplicate allocation guard
-        # Rule 6 — DISABLED
+        # Rule 6 — no duplicate allocation
+        if workload.status == WorkloadStatus.ALLOCATED:
+            raise WorkloadAlreadyAllocatedError(...)
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

| Version | Feature | Tests | Status |
|---|---|---|---|
| V1.1 | Base application — servers, workloads, allocations, best-fit engine | 58 | ✅ All green |
| V1.2 | Server status management, server deletion, workload eviction | 93 | ✅ All green |
| V1.3 | Workload delete, workload resource modification with delta accounting | 103 | ✅ All green |

---

*Document generated: 2026-08-15*  
*Repository: [github.com/Sriram-Selvaperumal/tactive-assignment](https://github.com/Sriram-Selvaperumal/tactive-assignment)*
