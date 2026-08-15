"""
Input validators for API request payloads.

All validation is done in the service/route boundary BEFORE any
business logic runs — enforcing Rule 10 (invalid requests rejected early).

Each validator returns a tuple:
    (is_valid: bool, errors: list[str])

This keeps validation logic decoupled from Flask request parsing.
"""

from __future__ import annotations

# ------------------------------------------------------------------ #
# Constants                                                            #
# ------------------------------------------------------------------ #

MAX_CPU = 10_000        # Reasonable upper bound for CPU cores
MAX_RAM = 1_048_576     # 1 TB in MB — generous upper bound


def validate_server_payload(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the JSON payload for POST /api/servers.

    Required fields:
        name          — non-empty string
        cpu_capacity  — positive integer
        ram_capacity  — positive integer (MB)

    Optional fields:
        server_type   — string, defaults to "general"
        status        — one of ONLINE / OFFLINE / MAINTENANCE
    """
    errors: list[str] = []

    # name
    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors.append("'name' is required and must be a non-empty string.")

    # cpu_capacity
    cpu = data.get("cpu_capacity")
    _validate_positive_int(cpu, "cpu_capacity", 1, MAX_CPU, errors)

    # ram_capacity
    ram = data.get("ram_capacity")
    _validate_positive_int(ram, "ram_capacity", 1, MAX_RAM, errors)

    # status (optional)
    status = data.get("status")
    if status is not None:
        valid_statuses = {"ONLINE", "OFFLINE", "MAINTENANCE"}
        if status not in valid_statuses:
            errors.append(f"'status' must be one of {sorted(valid_statuses)}.")

    return len(errors) == 0, errors


def validate_workload_payload(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the JSON payload for POST /api/workloads.

    Required fields:
        name          — non-empty string
        cpu_required  — positive integer
        ram_required  — positive integer (MB)
    """
    errors: list[str] = []

    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors.append("'name' is required and must be a non-empty string.")

    cpu = data.get("cpu_required")
    _validate_positive_int(cpu, "cpu_required", 1, MAX_CPU, errors)

    ram = data.get("ram_required")
    _validate_positive_int(ram, "ram_required", 1, MAX_RAM, errors)

    return len(errors) == 0, errors


def validate_allocation_payload(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the JSON payload for POST /api/allocations.

    Required fields:
        workload_id — non-empty string
    """
    errors: list[str] = []

    wid = data.get("workload_id")
    if not wid or not isinstance(wid, str) or not wid.strip():
        errors.append("'workload_id' is required and must be a non-empty string.")

    return len(errors) == 0, errors


# ------------------------------------------------------------------ #
# Private helpers                                                      #
# ------------------------------------------------------------------ #

def _validate_positive_int(
    value,
    field: str,
    min_val: int,
    max_val: int,
    errors: list[str],
) -> None:
    """Append an error message if value is not an integer in [min_val, max_val]."""
    if value is None:
        errors.append(f"'{field}' is required.")
        return
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"'{field}' must be an integer.")
        return
    if value < min_val:
        errors.append(f"'{field}' must be >= {min_val} (got {value}).")
    if value > max_val:
        errors.append(f"'{field}' must be <= {max_val} (got {value}).")
