# Offline verification — 0.6.3b3, 2026-10-15

Base: published 0.6.3b2, commit `76bd5114fa797b7f5dbb7661e7c769c44502f950`.

- Isolated `pytest -q`: **124 passed**.
- `python -m compileall -q custom_components tests`: passed.
- `git diff --check`: passed.
- Reviewed production delta: command preflight now shares the TTL-bounded coordinator position with the display; no independent overview request. Endpoint is rechecked after family resolution and consumed before activation. Packet builders and telemetry parser/listener are unchanged.

Regression coverage includes no-op at target, refusal for unknown/moving/intermediate/expired/offline position, avoiding one-shot telemetry, state change or expiry during family lookup, serialized queued calls, endpoint consumption and failed acknowledgements. Existing packet/parser/product-family/region/discovery tests also pass.

Tests are offline source/unit tests with fake HA collaborators. They do not attest full Home Assistant startup, real MQTT delivery or hardware command acceptance. No live broker, private credentials, HA service calls or motor actuation were used. Published-fork HACS/hassfest CI is a separate gate. Overall operational verdict: PARTIAL until supervised hardware acceptance. External controls can race the directionless trigger; no absolute-direction guarantee is claimed.
