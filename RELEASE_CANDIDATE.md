# 0.6.3b4 — initial stationary status bootstrap (UNPUBLISHED)

Base: a7c7d19 (published v0.6.3b3). Local changes only; no HA writes, motor commands, or broker sessions were executed.

## Findings

The persistent listener published connectionRequest and cmd 01 back-to-back, unlike the one-shot telemetry path, which waits for connectionRequestResponse. A device not yet ready can miss the early status wake; no bounded short retry existed. The initial coordinator refresh also classified a measured Wi-Fi serial before self.data existed, giving its stationary position 20 seconds instead of 90 seconds. Both are demonstrated code defects; their contribution to the specific installation symptom still needs hardware validation.

## Correction

After subscribing, request each known-MAC operator's session, await its non-retained connection response, then send only the existing cmd 01 identity/status packet. Network callbacks signal independent per-device events; the worker handles nonblocking progress, so silent devices do not block others. Missing acknowledgement or a fresh recognized position gets at most three attempts per 60-second refresh cycle, with a 15-second timeout for each handshake/status phase. An unknown measurement does not complete bootstrap. Stop/disconnect blocks further status requests. No cmd 03 activation/challenge echo, fabricated closed state, restored-position trust, or motor retry is introduced. Periodic idle refresh and 90/20-second stationary/moving TTLs remain.

Before initial coordinator data exists, measured Wi-Fi overview keys are recognized as Wi-Fi for the stationary TTL. Known GSM entries retain 20 seconds.

## Verification

136 offline source-level tests pass. Twelve targeted regressions fail against the published b3 production methods; the same cases pass with this correction. Coverage includes idle-open/closed startup, delayed ACK, a lost first response, bounded offline retries, independent devices, retained ACK/position rejection, unknown frames, stop, idle refresh, and no activation challenge echo. Source compilation and whitespace checks pass. These are mocked-transport/unit tests, not a full HA runtime or physical acceptance test. GitHub HACS/hassfest cannot validate this unpublished candidate yet.

## Installation and acceptance after separately authorized publication

1. Back up HA; in the existing fork's HACS entry explicitly select v0.6.3b4, download, then restart HA. Keep live status enabled; do not delete/recreate the integration.
2. Leave the physical operator stationary during restart. Do not use the remote/app to prime its status. Wait for network setup and the first measured frame; startup is not guaranteed to be instantaneous. Compare the displayed endpoint with the physical one.
3. If correct, the owner can separately test one dashboard operation with the movement area clear. Do not repeatedly click on errors.
4. Confirm idle status remains current beyond 90 seconds. Repeat restart at the other endpoint when convenient.
5. If no trustworthy telemetry arrives, leave the state unknown and collect sanitized diagnostics rather than forcing a motor pulse.

Rollback: explicitly select v0.6.3b3 in HACS and restart HA; it retains the startup defects. HACS commit/release selection is a separate known prerelease issue, not fixed by this candidate. No stable/latest release is claimed.
