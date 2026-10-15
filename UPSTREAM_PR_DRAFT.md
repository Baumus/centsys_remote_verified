# Prevent unverified HTTP position fallback on SMART covers

## Problem
A successful HTTP device/overview poll can leave SMART position showing closed while current device position differs. The live override expires independently of HTTP freshness, and successfully decoded poll telemetry does not become a live positional authority. Backend online does not prove current position feedback.

## Candidate change
Use bounded decoded non-retained MQTT position for SMART cover/operator status, with an expiry notification and no HTTP positional fallback. Add separate verified-feedback connectivity, clear trust on listener loss, reject failed SUBACK, and require a fresh endpoint before interpreting the directionless open/close trigger. Candidate idle cadence is 60s with a 90s stationary lifetime (20s for movement); this cadence/load tradeoff needs discussion and device validation rather than silent promotion.

## Evidence
113 offline tests pass; compile and whitespace checks pass. Tests are source/unit-level and do not claim a full HA or hardware test. No raw device messages, property details or credentials are included.

## Limits and maintainer questions
The missing MQTT stream trigger is not established. Can device idle telemetry reliably follow a 60s read-only wake without radio/power or app-session regressions? Is there an authoritative position timestamp/heartbeat to avoid a chosen freshness budget? Does the backend offer an absolute directional activation rather than TRG? Is stricter direction preflight preferred as a separate change? Hardware acceptance and HACS/hassfest remain pending.

This is a draft, not a submitted PR or an upstream-endorsed fix.
