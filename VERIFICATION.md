# Verification — 0.6.3 (2026-10-15)

Runtime behavior is unchanged from b5. 140 offline tests cover telemetry, position freshness, safe commands, acknowledged bounded startup and diagnostics. Test dependencies are in requirements-dev.txt. Release checks include pytest, compileall, git diff --check and GitHub HACS/Hassfest.

Tests use fake HA/transport collaborators, not a full HA runtime or physical devices. One owner reports successful stationary position acquisition and dashboard operation without remote/app priming, including a subsequent restart. Earlier b4 failed on that installation; the recovery mechanism is not established. Wider device/network validation remains open.

No credentials, raw logs or private installation details are included. Offline tests do not use real broker connections, HA calls or motor actuation. TRG remains directionless and external controls may race the final check; no automatic motor retry.
