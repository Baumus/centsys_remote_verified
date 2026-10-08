"""Tests for ``merge_devices`` (the remote-user + admin discovery union).

``api/models.py`` uses a relative import (``from . import enums``), so it is
loaded under a small synthetic package here, letting these tests run with plain
``pytest`` and no Home Assistant install (same shim as ``test_shared_access.py``).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_API = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "centsys_remote"
    / "api"
)

_pkg = types.ModuleType("centsys_api_shim_merge")
_pkg.__path__ = [str(_API)]  # type: ignore[attr-defined]
sys.modules["centsys_api_shim_merge"] = _pkg
for _name in ("enums", "models"):
    _spec = importlib.util.spec_from_file_location(
        f"centsys_api_shim_merge.{_name}", _API / f"{_name}.py"
    )
    assert _spec and _spec.loader
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[f"centsys_api_shim_merge.{_name}"] = _mod
    _spec.loader.exec_module(_mod)
models = sys.modules["centsys_api_shim_merge.models"]

Device = models.Device
merge_devices = models.merge_devices


def _device(serial: str, name: str = "") -> "models.Device":
    return Device.from_json({"serialNumber": serial, "deviceName": name or serial})


def test_union_of_disjoint_lists() -> None:
    # Each list has an operator the other lacks: both must survive the union.
    primary = [_device("AAA", "remote-only")]
    extra = [_device("BBB", "admin-only")]
    merged = merge_devices(primary, extra)
    assert [d.serial_number for d in merged] == ["AAA", "BBB"]


def test_overlap_is_deduped_primary_wins() -> None:
    # Same serial in both: kept once, with the primary (remote-user) record.
    primary = [_device("AAA", "from-remote")]
    extra = [_device("AAA", "from-admin")]
    merged = merge_devices(primary, extra)
    assert len(merged) == 1
    assert merged[0].serial_number == "AAA"
    assert merged[0].device_name == "from-remote"


def test_order_primary_first_then_admin_only() -> None:
    primary = [_device("AAA"), _device("BBB")]
    extra = [_device("BBB"), _device("CCC"), _device("AAA")]
    merged = merge_devices(primary, extra)
    assert [d.serial_number for d in merged] == ["AAA", "BBB", "CCC"]


def test_empty_serials_are_dropped() -> None:
    primary = [_device(""), _device("AAA")]
    extra = [_device(""), _device("BBB")]
    merged = merge_devices(primary, extra)
    assert [d.serial_number for d in merged] == ["AAA", "BBB"]


def test_admin_only_empty_leaves_primary_unchanged() -> None:
    primary = [_device("AAA"), _device("BBB")]
    merged = merge_devices(primary, [])
    assert [d.serial_number for d in merged] == ["AAA", "BBB"]


def test_both_empty() -> None:
    assert merge_devices([], []) == []


def test_duplicate_within_a_single_list_is_deduped() -> None:
    primary = [_device("AAA"), _device("AAA")]
    merged = merge_devices(primary, [])
    assert [d.serial_number for d in merged] == ["AAA"]
