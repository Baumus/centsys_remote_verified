# 0.6.3b3 — command preflight correction (pre-release; hardware acceptance pending)

Base: published 76bd5114fa797b7f5dbb7661e7c769c44502f950 (0.6.3b2).

The old action path always awaited `_read_overview(cached=False)` even when the persistent listener already supplied verified position. A missing/non-endpoint result blocked the action after the one-shot query, independently of the correct entity state. The initiating failure of that separate query has not been established.

This candidate shares the coordinator's freshness authority with the cover display. No new telemetry session is started for preflight, and no raw overview/HTTP position is trusted. Unknown/moving/intermediate/expired/offline states refuse immediately. The family lookup is followed by a final endpoint recheck; its consumed evidence cannot be reused by queued commands without new telemetry.

Verification: 124 offline source-level tests pass, compileall passes, whitespace check passes. No live broker, production installation, HA service call or hardware actuation used. Activation packets unchanged. Full HA startup and hardware acceptance untested; HACS/hassfest CI can run after publication.

After owner-authorized publication and passing CI: record the current version and retain a backup; select 0.6.3b3 in HACS, download and restart HA when safe. Keep live status enabled. First verify passive physical/HA agreement. Then perform a separate owner-supervised command acceptance with a clear movement area: opposite endpoint should activate once, same target should do nothing, moving/unknown should refuse promptly. No automatic command retries. Rollback: select 0.6.3b2 in HACS and restart; it retains the command-preflight defect.

Residual risk: TRG is directionless. External remote/app activity can race any preflight. Fresh position is bounded by the existing 90-second stationary policy, not a zero-age or absolute direction guarantee. Consumption may briefly show unknown until another measured frame arrives.
