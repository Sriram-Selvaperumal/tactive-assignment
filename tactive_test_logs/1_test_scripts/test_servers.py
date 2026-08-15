"""
test_servers.py — Server endpoint tests (V1 foundation).
"""

import pytest
from tests.conftest import make_server


class TestCreateServer:
    def test_create_valid_server(self, client):
        r = make_server(client, name="node-01", cpu=16, ram=32768)
        assert r.status_code == 201
        data = r.get_json()
        s = data["server"]
        assert s["name"] == "node-01"
        assert s["cpu_capacity"] == 16
        assert s["ram_capacity"] == 32768
        assert s["status"] == "ONLINE"
        assert s["allocated_cpu"] == 0
        assert s["allocated_ram"] == 0
        assert s["available_cpu"] == 16
        assert s["available_ram"] == 32768
        assert s["id"] is not None

    def test_duplicate_name_rejected(self, client):
        make_server(client, name="node-01")
        r = make_server(client, name="node-01")
        assert r.status_code == 409

    def test_missing_name_rejected(self, client):
        r = client.post("/api/servers", json={"cpu_capacity": 8, "ram_capacity": 16384})
        assert r.status_code == 400

    def test_negative_cpu_rejected(self, client):
        r = client.post("/api/servers", json={"name": "bad", "cpu_capacity": -1, "ram_capacity": 1024})
        assert r.status_code == 400

    def test_zero_ram_rejected(self, client):
        r = client.post("/api/servers", json={"name": "bad", "cpu_capacity": 8, "ram_capacity": 0})
        assert r.status_code == 400

    def test_invalid_status_rejected(self, client):
        r = client.post("/api/servers", json={"name": "bad", "cpu_capacity": 8, "ram_capacity": 1024, "status": "UNKNOWN"})
        assert r.status_code == 400


class TestListServers:
    def test_empty_list(self, client):
        r = client.get("/api/servers")
        assert r.status_code == 200
        assert r.get_json()["servers"] == []

    def test_lists_created_servers(self, client):
        make_server(client, name="node-01")
        make_server(client, name="node-02")
        r = client.get("/api/servers")
        assert r.status_code == 200
        assert len(r.get_json()["servers"]) == 2


class TestGetServer:
    def test_get_existing_server(self, client):
        created = make_server(client, name="node-01").get_json()["server"]
        r = client.get(f"/api/servers/{created['id']}")
        assert r.status_code == 200
        assert r.get_json()["server"]["name"] == "node-01"

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/api/servers/000000000000000000000000")
        assert r.status_code == 404

    def test_invalid_id_returns_404(self, client):
        r = client.get("/api/servers/not-a-valid-id")
        assert r.status_code == 404
