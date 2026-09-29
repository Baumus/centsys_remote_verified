"""Tests for datacentre-region selection.

Covers the two pure pieces of the region feature: ``region_for_country`` (how a
country maps to a datacentre, i.e. the "Auto" resolution) and the ``REGIONS``
endpoint table the client resolves its bases from. Both modules are plain stdlib
and are loaded straight from their file paths so the suite runs with bare
``pytest`` and no Home Assistant install.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "centsys_remote"


def _load(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / relpath)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


countries = _load("centsys_countries", "countries.py")
const = _load("centsys_api_const", "api/const.py")

region_for_country = countries.region_for_country


# --- region_for_country (the "Auto" resolution) ---------------------------


def test_australia_and_new_zealand_use_au() -> None:
    assert region_for_country("AU") == "au"
    assert region_for_country("NZ") == "au"


def test_south_africa_and_others_use_za() -> None:
    assert region_for_country("ZA") == "za"
    assert region_for_country("GB") == "za"
    assert region_for_country("US") == "za"


def test_default_country_resolves_to_za() -> None:
    assert region_for_country(countries.DEFAULT_COUNTRY) == "za"


def test_missing_or_blank_country_falls_back_to_za() -> None:
    assert region_for_country(None) == "za"
    assert region_for_country("") == "za"


def test_country_is_normalised() -> None:
    # Lower-case and surrounding whitespace still resolve.
    assert region_for_country(" au ") == "au"
    assert region_for_country("nz") == "au"


# --- REGIONS endpoint table (per-region base resolution) ------------------

_REQUIRED_KEYS = {"gateway", "gweb", "gweb_access", "gweb_smart", "mqtt"}


def test_default_region_is_za() -> None:
    assert const.DEFAULT_REGION == "za"
    assert const.DEFAULT_REGION in const.REGIONS


def test_both_regions_expose_the_same_endpoint_keys() -> None:
    assert set(const.REGIONS) == {"za", "au"}
    for region in const.REGIONS.values():
        assert set(region) == _REQUIRED_KEYS


def test_za_resolves_to_za_endpoints() -> None:
    za = const.REGIONS["za"]
    assert za["gateway"] == const.GATEWAY_URL_ZA
    assert za["gweb"] == const.GWEB_BASE
    assert za["gweb_access"] == const.GWEB_ACCESS_BASE
    assert za["gweb_smart"] == const.GWEB_SMART_BASE
    assert za["mqtt"] == const.MQTT_IP_ZA


def test_au_resolves_to_au_endpoints() -> None:
    au = const.REGIONS["au"]
    assert au["gateway"] == const.GATEWAY_URL_AU
    assert au["gweb"] == const.GWEB_BASE_AU
    assert au["gweb_access"] == const.GWEB_ACCESS_BASE_AU
    assert au["gweb_smart"] == const.GWEB_SMART_BASE_AU
    assert au["mqtt"] == const.MQTT_IP_AU


def test_the_two_regions_never_share_a_base() -> None:
    za, au = const.REGIONS["za"], const.REGIONS["au"]
    for key in _REQUIRED_KEYS:
        assert za[key] != au[key], key


def test_client_fallback_rule_selects_the_default_region() -> None:
    # Mirrors the client's ``REGIONS.get(region or DEFAULT_REGION, ...)``: an
    # entry with no stored region (None) lands on the default (ZA) datacentre.
    for region in (None, ""):
        resolved = const.REGIONS.get(region or const.DEFAULT_REGION, const.REGIONS[const.DEFAULT_REGION])
        assert resolved is const.REGIONS["za"]
