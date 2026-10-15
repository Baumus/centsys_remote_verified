# Offline verification — 2026-10-15

Base: upstream `7c05bec3b83a296cd0dce5548cc2fef6d08b1f77` (post-0.6.3b1).
Candidate: manifest 0.6.3b2, isolated branch `fix/hacs-verified-position`.

Observed results:
- `pytest -q (isolated test environment)`: **113 passed in 0.22s**.
- `python3 -m compileall -q custom_components`: passed.
- `git diff HEAD --check`: passed.
- Final manual diff review: position authority, timers, listener disconnect, retained-frame rejection, subscription failure, endpoint preflight and local command serialization reviewed. No changes to activation packet builders. Original MIT license retained.

Covered regressions include HTTP-closed vs MQTT-open, poll and listener ingestion, timer notification/cancellation, unknown/lost input, stationary/moving TTLs, cloud-offline, disconnect/reconnect policy, retained telemetry, rejected subscription, no-op at target endpoint, refusal at unknown/moving/intermediate state and serialization of concurrent HA actions. Existing upstream packet/parser/product-family/region/discovery/legacy tests also pass.

No tests used property credentials or a live broker; no HA service calls, installation, reloads or actuation occurred. The AST-based position tests execute selected production methods with fake HA collaborators; they do not attest complete entity registration, config-entry setup or real MQTT delivery. HACS/hassfest validation and full HA runtime startup have not run here. Dashboard YAML is a draft; no rendered visual QA. Overall operational verdict: PARTIAL, pending published-fork CI and supervised hardware acceptance. The cause of the absent live data is not proven fixed.
