# Tactive User Guide
### DataCentre Allocator — Complete Setup, Usage & Architecture Reference

**Version:** V1.3  
**Stack:** Python · Flask · MongoDB Atlas · HTML / CSS / JavaScript  
**Repository:** [github.com/Sriram-Selvaperumal/tactive-assignment](https://github.com/Sriram-Selvaperumal/tactive-assignment)

---

## Table of Contents

**Part 1 — Running the Application**
1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Set Up the Python Environment](#3-set-up-the-python-environment)
4. [Configure MongoDB Atlas](#4-configure-mongodb-atlas)
5. [Configure Environment Variables](#5-configure-environment-variables)
6. [Run the Application](#6-run-the-application)
7. [Run the Automated Tests](#7-run-the-automated-tests)

**Part 2 — Using the Application**

8. [Application Overview](#8-application-overview)
9. [Managing Servers](#9-managing-servers)
10. [Managing Workloads](#10-managing-workloads)
11. [Allocating Workloads to Servers](#11-allocating-workloads-to-servers)
12. [API Reference](#12-api-reference)

**Part 3 — Architecture & Design**

13. [High-Level Architecture](#13-high-level-architecture)
14. [Layered Architecture Deep Dive](#14-layered-architecture-deep-dive)
15. [Domain Models](#15-domain-models)
16. [Allocation Engine — Business Rules](#16-allocation-engine--business-rules)
17. [Best-Fit Scheduling Strategy](#17-best-fit-scheduling-strategy)
18. [Database Design](#18-database-design)
19. [Error Handling Model](#19-error-handling-model)
20. [Project File Structure](#20-project-file-structure)

---

# Part 1 — Running the Application

## 1. Prerequisites

Before you start, make sure you have the following installed on your machine:

| Tool | Minimum Version | How to Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any recent | `git --version` |
| A web browser | Chrome / Firefox / Edge | — |

You will also need a free **MongoDB Atlas** account (cloud-hosted database). Setup instructions are in [Step 4](#4-configure-mongodb-atlas).

---

## 2. Clone the Repository

Open a terminal (Command Prompt or PowerShell on Windows) and run:

```powershell
git clone https://github.com/Sriram-Selvaperumal/tactive-assignment.git
cd tactive-assignment\tactive_project
```

This puts you inside the Flask application directory, which is where all remaining commands should be run.

---

## 3. Set Up the Python Environment

It is strongly recommended to use a **virtual environment** so that project dependencies are isolated from the rest of your system.

### Step 3.1 — Create the Virtual Environment

```powershell
python -m venv venv
```

This creates a `venv/` folder in your current directory containing a clean Python installation.

### Step 3.2 — Activate the Virtual Environment

```powershell
# Windows (PowerShell)
venv\Scripts\activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

Once activated, you will see `(venv)` at the beginning of your terminal prompt. This confirms you are working inside the virtual environment.

### Step 3.3 — Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs the following packages:

| Package | Purpose |
|---|---|
| `Flask 3.1.3` | Web framework — routes, request/response handling |
| `pymongo 4.10.1` | MongoDB driver for Python |
| `python-dotenv 1.1.1` | Loads environment variables from `.env` file |
| `pytest 8.3.5` | Test framework |
| `pytest-flask 1.3.0` | Flask integration for pytest |
| `Werkzeug 3.1.8` | WSGI utilities used by Flask |
| `blinker 1.9.0` | Signal support for Flask |

---

## 4. Configure MongoDB Atlas

The application uses **MongoDB Atlas** — a free, cloud-hosted MongoDB service. Follow these steps to get your database connection string.

### Step 4.1 — Create an Atlas Account
1. Go to [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for a free account and log in

### Step 4.2 — Create a Cluster
1. Click **"Build a Database"**
2. Select **"M0 Free"** tier
3. Choose a cloud provider and region (any region works)
4. Name your cluster (e.g., `tactive`)
5. Click **"Create"** and wait ~2 minutes for it to provision

### Step 4.3 — Create a Database User
1. In the left sidebar, click **"Database Access"**
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Enter a username (e.g., `tactive`) and a strong password
5. Set the role to **"Read and Write to Any Database"**
6. Click **"Add User"**

### Step 4.4 — Configure Network Access
1. In the left sidebar, click **"Network Access"**
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (adds `0.0.0.0/0`)
4. Click **"Confirm"**

> **Note:** For production, you would restrict this to specific IP addresses. For development, allowing all IPs is acceptable.

### Step 4.5 — Get Your Connection String
1. In the left sidebar, click **"Database"**
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Select **Driver: Python**, **Version: 3.6 or later**
5. Copy the connection string — it will look like:
   ```
   mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<username>`, `<password>`, and `<cluster>` with your actual values

---

## 5. Configure Environment Variables

The application reads its configuration from a `.env` file. A template is provided.

### Step 5.1 — Copy the Template

```powershell
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### Step 5.2 — Edit the `.env` File

Open `.env` in any text editor and fill in your values:

```env
# MongoDB connection string from Step 4.5
MONGO_URI=mongodb+srv://tactive:yourpassword@yourcluster.mongodb.net/?retryWrites=true&w=majority&appName=tactive

# Name of the database to use (will be created automatically if it doesn't exist)
MONGO_DBNAME=datacenter_db

# Application environment: development | testing | production
APP_ENV=development

# A random secret key for Flask session security
SECRET_KEY=replace-this-with-a-random-string
```

> **Important:** Never commit your `.env` file to Git. It is already listed in `.gitignore` to prevent this.

---

## 6. Run the Application

With the virtual environment active and `.env` configured, start the Flask development server:

```powershell
python run.py
```

You should see output like:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open your browser and navigate to:

```
http://localhost:5000
```

The application's single-page interface will load and you can begin using it.

---

## 7. Run the Automated Tests

The test suite uses a separate database (`datacenter_test_db`) so it never touches your development data. Each test cleans up after itself.

```powershell
# Make sure virtual environment is active, then run:
venv\Scripts\python.exe -m pytest tests/ -v
```

A successful run looks like:

```
tests/test_allocations.py::TestRule1OnlineOnly::...    PASSED
tests/test_allocations.py::TestRule6NoDuplicateAllocation::... PASSED
...
======================= 103 passed in 115.14s =======================
```

### Useful Test Flags

```powershell
# Run only allocation tests
venv\Scripts\python.exe -m pytest tests/test_allocations.py -v

# Run a specific test class
venv\Scripts\python.exe -m pytest tests/test_allocations.py::TestRule7BestFitStrategy -v

# Show short traceback on failures
venv\Scripts\python.exe -m pytest tests/ -v --tb=short

# Stop on first failure
venv\Scripts\python.exe -m pytest tests/ -v -x
```

---

# Part 2 — Using the Application

## 8. Application Overview

The DataCentre Allocator is a resource management tool for a simulated data centre. Its core job is to assign computational workloads to physical or virtual servers in an efficient way.

There are three core concepts:

| Concept | Description |
|---|---|
| **Server** | A physical or virtual machine with a fixed amount of CPU cores and RAM |
| **Workload** | A computational task that requires a specific amount of CPU cores and RAM to run |
| **Allocation** | The assignment of a workload to a server that has sufficient available resources |

The UI is a minimal single-page application. All data is loaded dynamically via REST API calls — no page reloads needed.

---

## 9. Managing Servers

### Add a Server
1. In the **Servers** section, fill in:
   - **Name** — unique identifier (e.g., `web-server-01`)
   - **CPU Capacity** — total CPU cores (1 – 10,000)
   - **RAM Capacity** — total RAM in MB (1 – 1,048,576)
2. Click **"Add Server"**

The server appears in the list with status `ONLINE` and zero allocated resources.

### Server Status
Each server has one of three statuses:

| Status | Meaning | Accepts New Workloads? |
|---|---|---|
| 🟢 **ONLINE** | Server is active and available | Yes |
| 🔴 **OFFLINE** | Server is powered down | No |
| 🟡 **MAINTENANCE** | Server is undergoing maintenance | No |

To change a server's status, click the status toggle button on the server card. If you move a server to **Offline** or **Maintenance**, all workloads currently allocated to it are automatically **re-queued** (set back to `PENDING`).

### Delete a Server
Click the **"Delete"** button on a server card. A confirmation dialog will appear. Confirming permanently deletes the server and re-queues all of its allocated workloads.

---

## 10. Managing Workloads

### Add a Workload
1. In the **Workloads** section, fill in:
   - **Name** — unique identifier (e.g., `batch-job-42`)
   - **CPU Required** — CPU cores needed (1 – 10,000)
   - **RAM Required** — RAM needed in MB (1 – 1,048,576)
2. Click **"Add Workload"**

Every new workload starts with status **`PENDING`** — it has not yet been assigned to any server.

### Workload Status

| Status | Meaning |
|---|---|
| ⏳ **PENDING** | Waiting to be allocated to a server |
| ✅ **ALLOCATED** | Currently running on an assigned server |

### Edit a Workload's Resources
Click the **"Edit"** button on a workload card and enter new CPU and RAM values. The system will validate that the server has enough available capacity before applying the change.

### Delete a Workload
Click the **"Delete"** button on a workload card and confirm. If the workload is allocated, the server's resources are freed automatically before deletion.

---

## 11. Allocating Workloads to Servers

### Trigger Allocation
1. Find a workload with **`PENDING`** status
2. Click **"Allocate"**
3. The system automatically selects the most suitable server and assigns the workload

### What Happens Under the Hood
1. The system scans all **ONLINE** servers
2. It filters out servers that don't have enough CPU *and* RAM
3. Among eligible servers, it picks the one with the **tightest fit** (smallest leftover capacity after placement)
4. The workload status changes to `ALLOCATED`, the server's resource counters are updated, and an allocation record is created

### When Allocation Fails
| Reason | Error Shown |
|---|---|
| No ONLINE servers exist | `No ONLINE server has sufficient CPU and RAM` |
| All ONLINE servers are full | `No ONLINE server has sufficient CPU and RAM` |
| Workload is already allocated | `Workload is already allocated` |

---

## 12. API Reference

The application exposes a REST API. All endpoints return JSON.

### Servers

| Method | Endpoint | Description | Success Code |
|---|---|---|---|
| `POST` | `/api/servers` | Create a new server | `201` |
| `GET` | `/api/servers` | List all servers | `200` |
| `GET` | `/api/servers/<id>` | Get a server by ID | `200` |
| `PATCH` | `/api/servers/<id>/status` | Update server status | `200` |
| `DELETE` | `/api/servers/<id>` | Delete a server | `200` |

**Create Server — Request Body:**
```json
{
  "name": "web-server-01",
  "cpu_capacity": 16,
  "ram_capacity": 32768,
  "server_type": "general",
  "status": "ONLINE"
}
```

**Update Status — Request Body:**
```json
{ "status": "MAINTENANCE" }
```

---

### Workloads

| Method | Endpoint | Description | Success Code |
|---|---|---|---|
| `POST` | `/api/workloads` | Create a new workload | `201` |
| `GET` | `/api/workloads` | List all workloads | `200` |
| `GET` | `/api/workloads/<id>` | Get a workload by ID | `200` |
| `PATCH` | `/api/workloads/<id>` | Modify CPU/RAM allocation | `200` |
| `DELETE` | `/api/workloads/<id>` | Delete a workload | `200` |

**Create Workload — Request Body:**
```json
{
  "name": "batch-job-42",
  "cpu_required": 4,
  "ram_required": 8192
}
```

**Modify Resources — Request Body:**
```json
{
  "cpu_required": 6,
  "ram_required": 12288
}
```

---

### Allocations

| Method | Endpoint | Description | Success Code |
|---|---|---|---|
| `POST` | `/api/allocations` | Allocate a workload to a server | `201` |
| `GET` | `/api/allocations/<id>` | Get an allocation record | `200` |

**Allocate — Request Body:**
```json
{ "workload_id": "<workload-id-string>" }
```

**Successful Allocation Response:**
```json
{
  "ok": true,
  "data": {
    "allocation": { "id": "...", "workload_id": "...", "server_id": "...", "created_at": "..." },
    "workload": { "id": "...", "name": "batch-job-42", "status": "ALLOCATED", ... },
    "server":   { "id": "...", "name": "web-server-01", "allocated_cpu": 4, ... }
  }
}
```

---

### Health Check

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns `{ "status": "ok" }` if the app is running |

---

### Error Response Format

All error responses follow a consistent structure:

```json
{
  "ok": false,
  "error": "Human-readable error message.",
  "details": ["Optional list of specific validation errors"]
}
```

Common HTTP status codes used:

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Resource created |
| `400` | Bad request / validation failure |
| `404` | Resource not found |
| `409` | Conflict (duplicate name, already allocated, insufficient resources) |
| `500` | Unexpected server error |

---

# Part 3 — Architecture & Design

## 13. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         Browser (Client)                       │
│                                                               │
│   index.html  ←→  style.css  ←→  app.js (Vanilla JS SPA)     │
│                       ↕ HTTP / JSON (fetch API)               │
└───────────────────────────────────────────────────────────────┘
                              ↕
┌───────────────────────────────────────────────────────────────┐
│                      Flask Application                         │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                     Routes Layer                        │   │
│  │    /api/servers  /api/workloads  /api/allocations       │   │
│  │    Input validation → call service → format response    │   │
│  └───────────────────────┬────────────────────────────────┘   │
│                          ↓                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                   Service Layer                          │   │
│  │              AllocationService                           │   │
│  │   Business rules · Best-fit algorithm · Eviction logic  │   │
│  └───────────────────────┬────────────────────────────────┘   │
│                          ↓                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                 Repository Layer                         │   │
│  │  ServerRepository · WorkloadRepository · AllocRepo      │   │
│  │         Pure CRUD — translates between Python ↔ MongoDB  │   │
│  └───────────────────────┬────────────────────────────────┘   │
└──────────────────────────┼────────────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────────────┐
│                    MongoDB Atlas (Cloud)                        │
│                                                               │
│   datacenter_db                                               │
│   ├── servers        (documents)                              │
│   ├── workloads      (documents)                              │
│   └── allocations    (documents)                              │
└───────────────────────────────────────────────────────────────┘
```

---

## 14. Layered Architecture Deep Dive

The application is structured around a strict four-layer separation of concerns. Each layer has one job and is not allowed to reach into another layer's responsibility.

### Layer 1 — Routes (`app/routes/`)
**Responsibility:** HTTP only.

- Parse incoming JSON from the request body
- Run input validation
- Call the appropriate service method
- Catch typed exceptions and map them to HTTP status codes
- Return a formatted JSON response

Routes contain **zero business logic**. They do not know what "best fit" means or when a workload should be evicted. They only know how to translate HTTP requests into service calls.

```python
# Example: routes/allocations.py
@bp.post("/api/allocations")
def create_allocation():
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_allocation_payload(data)
    if not is_valid:
        return error("Validation failed.", 400, errors)
    try:
        result = _service().allocate(data["workload_id"].strip())
        return success(result.to_dict(), 201)
    except WorkloadNotFoundError as exc:
        return error(str(exc), 404)
    except NoEligibleServerError as exc:
        return error(str(exc), 409)
```

### Layer 2 — Service (`app/services/`)
**Responsibility:** Business logic and orchestration.

- This is the most important layer in the application
- All allocation rules are enforced here and **only** here
- Coordinates multi-step operations across repositories (e.g., eviction: update workloads → delete allocations → reset server)
- Raises typed Python exceptions — never returns HTTP status codes
- Has no knowledge of Flask or HTTP

```python
# Example: services/allocation_service.py
class AllocationService:
    def allocate(self, workload_id: str) -> AllocationResult:
        # Rule 6 — no duplicate allocation
        if workload.status == WorkloadStatus.ALLOCATED:
            raise WorkloadAlreadyAllocatedError(...)
        # Rules 1, 2, 3, 4 — eligible server selection
        eligible = [s for s in online_servers
                    if s.available_cpu >= workload.cpu_required
                    and s.available_ram >= workload.ram_required]
        # Rule 7 — best-fit selection
        selected_server = self._best_fit(eligible, workload)
        ...
```

### Layer 3 — Repositories (`app/repositories/`)
**Responsibility:** Database access only.

- Translate between Python domain objects and MongoDB documents
- Execute all MongoDB queries
- Contain **no business logic** — they simply store and retrieve data
- Can be swapped for a different database without changing any service or route code

```python
# Example: repositories/server_repository.py
def get_online(self) -> list[Server]:
    """Return all servers with status ONLINE."""
    docs = self._col.find({"status": "ONLINE"}).sort("created_at", 1)
    return [Server.from_doc(d) for d in docs]
```

### Layer 4 — Domain Models (`app/models/`)
**Responsibility:** Data shape and computed properties.

- Pure Python dataclasses — no database coupling, no Flask coupling
- Define the structure of `Server`, `Workload`, and `Allocation`
- Include computed properties (e.g., `available_cpu = cpu_capacity - allocated_cpu`)
- Include `to_dict()` for JSON serialisation and `from_doc()` for deserialisation from MongoDB

---

## 15. Domain Models

### Server

| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `name` | `str` | Unique server name |
| `cpu_capacity` | `int` | Total CPU cores |
| `ram_capacity` | `int` | Total RAM in MB |
| `server_type` | `str` | General / compute / etc. |
| `status` | `ServerStatus` | ONLINE / OFFLINE / MAINTENANCE |
| `allocated_cpu` | `int` | CPU cores currently in use |
| `allocated_ram` | `int` | RAM currently in use (MB) |
| `available_cpu` _(computed)_ | `int` | `cpu_capacity - allocated_cpu` |
| `available_ram` _(computed)_ | `int` | `ram_capacity - allocated_ram` |
| `cpu_utilisation_pct` _(computed)_ | `float` | % of CPU used |
| `ram_utilisation_pct` _(computed)_ | `float` | % of RAM used |

### Workload

| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `name` | `str` | Unique workload name |
| `cpu_required` | `int` | CPU cores needed |
| `ram_required` | `int` | RAM needed in MB |
| `status` | `WorkloadStatus` | PENDING / ALLOCATED |

### Allocation

| Field | Type | Description |
|---|---|---|
| `id` | `str` | MongoDB ObjectId |
| `workload_id` | `str` | Reference to the workload |
| `server_id` | `str` | Reference to the server |
| `created_at` | `datetime` | When the allocation was made |

---

## 16. Allocation Engine — Business Rules

The `AllocationService.allocate()` method enforces 10 rules in a defined sequence:

| Rule | Name | Description |
|---|---|---|
| 1 | ONLINE Only | Only servers with status `ONLINE` are considered |
| 2 | CPU Sufficiency | Server must have `available_cpu >= workload.cpu_required` |
| 3 | RAM Sufficiency | Server must have `available_ram >= workload.ram_required` |
| 4 | Both Required | Rules 2 and 3 must both pass — one alone is not enough |
| 5 | No Partial Allocation | If no server is eligible, nothing is written — state is unchanged |
| 6 | No Duplicate Allocation | A workload that is already `ALLOCATED` cannot be allocated again |
| 7 | Best-Fit Selection | Among eligible servers, select the one with the least remaining slack |
| 8 | Resource Accounting | After allocation, the server's `allocated_cpu` and `allocated_ram` are incremented |
| 9 | Status Consistency | After allocation, the workload's status transitions from `PENDING` to `ALLOCATED` |
| 10 | Input Validation | Missing or malformed `workload_id` is rejected with `400 Bad Request` |

### Eviction Rules (V1.2)

When a server is taken **Offline**, put into **Maintenance**, or **Deleted**, the following eviction sequence runs automatically for every workload assigned to that server:

```
For each allocated workload on the affected server:
  1. Reset workload status → PENDING
  2. Delete the allocation record
After all workloads are re-queued:
  3. Reset server's allocated_cpu and allocated_ram to 0
  4. Apply the status change (or delete) to the server
```

This ensures no workload is left stranded in `ALLOCATED` state with an invalid server reference.

---

## 17. Best-Fit Scheduling Strategy

When multiple servers are eligible for a workload, the engine picks the one that results in the **tightest packing** — the server with the least remaining free capacity after placement.

### Scoring Formula

```
score = (available_cpu − required_cpu) + (available_ram − required_ram)
```

The server with the **lowest score wins** (smallest leftover = tightest fit).

### Example

A workload needs 4 CPU cores and 8 GB RAM.

| Server | Available CPU | Available RAM | Score |
|---|---|---|---|
| Server A | 16 | 32768 MB | (16−4) + (32768−8192) = **24,588** |
| Server B | 8 | 16384 MB | (8−4) + (16384−8192) = **8,196** |
| Server C | 4 | 8192 MB | (4−4) + (8192−8192) = **0** ✅ |

**Server C is selected** — it is the tightest fit.

### Why Best-Fit?
- Maximises overall cluster utilisation by filling servers to capacity before using new ones
- Deterministic and predictable — easy to reason about and test
- Tie-broken by oldest insertion order (first registered server is preferred)

---

## 18. Database Design

The application uses three MongoDB collections inside the `datacenter_db` database:

### `servers` Collection

```json
{
  "_id": ObjectId("..."),
  "name": "web-server-01",
  "cpu_capacity": 16,
  "ram_capacity": 32768,
  "server_type": "general",
  "status": "ONLINE",
  "allocated_cpu": 4,
  "allocated_ram": 8192,
  "created_at": ISODate("2026-08-14T10:00:00Z"),
  "updated_at": ISODate("2026-08-14T10:05:00Z")
}
```

**Indexes:** Unique index on `name`.

---

### `workloads` Collection

```json
{
  "_id": ObjectId("..."),
  "name": "batch-job-42",
  "cpu_required": 4,
  "ram_required": 8192,
  "status": "ALLOCATED",
  "created_at": ISODate("2026-08-14T10:02:00Z"),
  "updated_at": ISODate("2026-08-14T10:05:00Z")
}
```

**Indexes:** Unique index on `name`.

---

### `allocations` Collection

```json
{
  "_id": ObjectId("..."),
  "workload_id": "686dc...",
  "server_id": "686da...",
  "created_at": ISODate("2026-08-14T10:05:00Z")
}
```

**Indexes:** Unique index on `workload_id` (one allocation per workload).

---

### Multi-Document Consistency

MongoDB Atlas free-tier does not support multi-document ACID transactions without a dedicated replica set. This application handles consistency through a **compensating operations pattern**:

- Operations are sequenced so that the most critical write happens first
- Each subsequent step logically compensates for the previous one
- A unique index on `workload_id` in the `allocations` collection acts as a race condition guard — concurrent allocation requests for the same workload will have one succeed and one fail with a `DuplicateKeyError`

---

## 19. Error Handling Model

The application uses a **typed exception hierarchy** to cleanly separate what went wrong from how to report it.

```
AllocationError  (base)
├── WorkloadNotFoundError          → HTTP 404
├── WorkloadAlreadyAllocatedError  → HTTP 409
├── NoEligibleServerError          → HTTP 409
└── ServerNotFoundError            → HTTP 404
```

The service layer raises typed exceptions. The route layer catches them and maps them to the appropriate HTTP response code. This means:

- **Service layer** never knows what HTTP means
- **Route layer** never knows what business rules mean
- Adding a new error type requires only: a new exception class + one `except` clause in the route

All error responses use the same JSON envelope:

```json
{
  "ok": false,
  "error": "Workload 'batch-job-42' is already allocated.",
  "details": []
}
```

---

## 20. Project File Structure

```
tactive_project/
│
├── run.py                          ← Entry point — starts Flask dev server
├── requirements.txt                ← Python dependencies
├── pytest.ini                      ← Pytest configuration
├── .env.example                    ← Environment variable template (safe to commit)
├── .env                            ← Actual secrets (gitignored)
│
├── app/
│   ├── __init__.py                 ← create_app() factory — wires up the app
│   ├── config.py                   ← Dev / Test / Prod configuration classes
│   ├── errors.py                   ← success() / error() response helpers + error handlers
│   │
│   ├── database/
│   │   └── __init__.py             ← MongoClient singleton — one connection shared per request
│   │
│   ├── models/
│   │   ├── server.py               ← Server dataclass + ServerStatus enum
│   │   ├── workload.py             ← Workload dataclass + WorkloadStatus enum
│   │   └── allocation.py           ← Allocation dataclass
│   │
│   ├── repositories/
│   │   ├── server_repository.py    ← MongoDB CRUD for servers
│   │   ├── workload_repository.py  ← MongoDB CRUD for workloads
│   │   └── allocation_repository.py← MongoDB CRUD for allocations
│   │
│   ├── services/
│   │   └── allocation_service.py   ← All business rules + best-fit algorithm
│   │
│   ├── validators/
│   │   └── request_validators.py   ← Input validation for server/workload/allocation payloads
│   │
│   └── routes/
│       ├── health.py               ← GET /api/health
│       ├── servers.py              ← Server CRUD + status update + delete endpoints
│       ├── workloads.py            ← Workload CRUD + modify + delete endpoints
│       └── allocations.py          ← Allocation submit + retrieve endpoints
│
├── static/
│   ├── css/style.css               ← Application stylesheet
│   └── js/app.js                   ← Single-page app logic (fetch API + DOM rendering)
│
├── templates/
│   └── index.html                  ← SPA shell — served once, JS handles all updates
│
└── tests/
    ├── conftest.py                 ← Pytest fixtures, test Flask app, DB teardown
    ├── test_servers.py             ← Server endpoint tests
    ├── test_workloads.py           ← Workload endpoint tests
    └── test_allocations.py         ← Allocation business rule tests (103 total)
```

---

*DataCentre Allocator — Tactive SDLC Assessment*  
*Repository: [github.com/Sriram-Selvaperumal/tactive-assignment](https://github.com/Sriram-Selvaperumal/tactive-assignment)*
