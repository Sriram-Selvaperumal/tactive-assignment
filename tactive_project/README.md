# DataCentre Allocator — V1.1

A minimal Flask + MongoDB REST API for data-centre resource allocation.  
Built as an SDLC assessment project for Tactive.

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- MongoDB running locally on `mongodb://localhost:27017`

### 2. Clone and set up virtual environment

```bash
# (already done in workspace — activate the existing venv)
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Edit .env if your MongoDB URI differs from the default
```

### 5. Run the application

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/servers` | Create a server |
| GET | `/api/servers` | List all servers |
| GET | `/api/servers/<id>` | Get a server by ID |
| POST | `/api/workloads` | Create a workload |
| GET | `/api/workloads` | List all workloads |
| GET | `/api/workloads/<id>` | Get a workload by ID |
| POST | `/api/allocations` | Allocate a workload |
| GET | `/api/allocations/<id>` | Get an allocation |

---

## Run Tests

```bash
venv\Scripts\pytest tests\ -v
```

> Tests use a separate database (`datacenter_test_db`) and clean up after each test.  
> **Requires MongoDB running locally.**

---

## Project Structure

```
app/
├── __init__.py          # create_app() factory
├── config.py            # Dev / Test / Prod config
├── database/            # MongoDB connection
├── models/              # Domain models (Server, Workload, Allocation)
├── repositories/        # DB access layer
├── services/            # Business logic (AllocationService)
├── validators/          # Input validation
├── routes/              # Flask blueprints
└── errors.py            # Centralized error handling
```
