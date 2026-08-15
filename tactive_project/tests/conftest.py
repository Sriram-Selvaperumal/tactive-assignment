"""
conftest.py — pytest fixtures for V1 test foundation.

Uses a dedicated test MongoDB database (datacenter_test_db).
Each test function gets a fresh database via the autouse fixture.

Usage:
    pytest tests/
"""

import pytest
from app import create_app
from app.config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create the Flask application in testing mode (once per session)."""
    return create_app(TestingConfig)


@pytest.fixture()
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """
    Drop all collections before each test to guarantee isolation.
    Runs automatically for every test function.
    """
    db = app.db
    db["servers"].drop()
    db["workloads"].drop()
    db["allocations"].drop()
    # Re-create indexes after dropping
    db["servers"].create_index("name", unique=True)
    db["workloads"].create_index("name", unique=True)
    db["allocations"].create_index("workload_id", unique=True)
    yield
    # No teardown needed — next test will clean before running


# ------------------------------------------------------------------ #
# Shared helper factories                                              #
# ------------------------------------------------------------------ #

def make_server(client, name="node-01", cpu=16, ram=32768, status="ONLINE"):
    """POST /api/servers and return the response JSON."""
    r = client.post("/api/servers", json={
        "name": name,
        "cpu_capacity": cpu,
        "ram_capacity": ram,
        "status": status,
    })
    return r


def make_workload(client, name="job-01", cpu=4, ram=8192):
    """POST /api/workloads and return the response JSON."""
    r = client.post("/api/workloads", json={
        "name": name,
        "cpu_required": cpu,
        "ram_required": ram,
    })
    return r
