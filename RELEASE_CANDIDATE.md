# 0.6.3 — release and upgrade notes

Regular verified-state fork release. Runtime behavior is unchanged from b5; this release updates version/packaging/docs and incorporates offline dependency PR #2. b5 added diagnostics, not an additional startup fix.

## Behavior and evidence

SMART position requires fresh non-retained MQTT feedback. Startup/reconnect waits for connection acknowledgement before requesting identity/status, with at most three attempts per 60-second cycle and 15-second phase timeouts. Stationary/moving position lifetimes are 90/20 seconds. Unknown/stale/offline feedback fails closed; HTTP online is not position evidence. Status requests do not move the operator.

Commands recheck and consume a verified endpoint before sending. TRG remains directionless and external controls can race the final check. No motor retry or absolute-direction guarantee.

140 offline regressions cover freshness, safe commands, startup, delayed/missing/retained replies, independent devices and diagnostics. One installation reports correct stationary startup and dashboard operation without remote/app priming, also after a subsequent HA restart. Earlier b4 failed there; the eventual recovery mechanism is unproven. This is limited field evidence, not validation for all devices/networks.

## Upgrade and rollback

1. Back up HA. In the existing fork HACS entry download regular **v0.6.3**, then restart HA in a safe maintenance window. Keep live status enabled; do not delete/recreate the integration or install two providers for this domain.
2. Leave the operator stationary without remote/app operation. Allow network setup and the first measured status, then compare the display with the physical position.
3. If trustworthy feedback is absent, leave the state unknown and collect sanitized diagnostics. Never initialize using automatic movement.

Rollback: select **v0.6.3b5** in HACS and restart HA; this restores the preceding runtime-equivalent prerelease. Publishing does not change HA or trigger hardware.
