# Verified position 0.6.3b2 — pre-release, not hardware accepted

## Scope and semantics

- SMART cover and operator-status sensor read decoded, non-retained MQTT position; HTTP metadata can no longer masquerade as a current open/closed measurement.
- Freshness is bounded: stationary Wi-Fi positions expire at 90 seconds; moving positions expire at 20 seconds. An expiry timer updates HA even with no subsequent frame. Unknown/lost measurements invalidate the previous endpoint immediately. Cloud-offline also makes the positional view unknown.
- With **Enable live status** enabled, idle read-only wakes run every 60 seconds (previous upstream cadence: 600 seconds). This candidate deliberately changes radio/network load. Device idle delivery cadence, coexistence with the app and power impact need hardware acceptance. Without that listener, long unknown intervals are expected: the slower legacy poll is unchanged.
- A lost active listener session clears Wi-Fi positional trust immediately. Successful broker subscription alone never counts as a fresh device position. Failed SUBACK is rejected rather than counted as connected.
- New **Verified telemetry** connectivity sensor means a recent usable positional frame and successful coordinator/device health, NOT merely TCP, Wi-Fi, or cloud reachability. “Off” means position feedback is not verified, not proof the motor has lost power. The existing **Online** remains a distinct backend-reported signal.
- Open and close preflight require a newly requested stationary endpoint. At the requested endpoint they are no-ops; unknown, moving and intermediate states refuse to actuate. Local HA calls are serialized. The underlying operator command is still a directionless trigger; outside app/remote activity may race this check. There is no absolute-direction guarantee and no movement on startup added by this patch.
- GSM/shared behavior is not the target; GSM keeps the original 20-second live lifetime. New freshness policy does not fix unrelated legacy stale fallbacks.

## Verification and release gate

See `VERIFICATION.md` for exact automated evidence and limitations. Tests are offline source/unit tests with deterministic collaborators, not a complete Home Assistant startup, HACS/hassfest run or device test. The missing live-stream cause remains unresolved. This candidate must NOT be sold as a proven functional repair.

Before promotion: run HACS validation and hassfest in the published fork, then supervised device acceptance: real open status, idle > 90 seconds without false closed, app coexistence, one authorized close/open cycle, loss of feedback => unverified/unknown, reconnect => current state. Also assess idle wake load. Do not tune a TTL merely to hide missing telemetry.

## HACS installation plan (after fork publication and validation)

1. Record installed version and repository. Take and verify a recoverable HA backup (config, integration files, config entries and entity registry); do not delete/re-add the integration.
2. Ensure no existing automation can operate this cover during the supervised test window. Installation/restart is not an actuation test, but startup automation must be reviewed separately.
3. In HACS, switch the source for `centsys_remote` to the published custom Integration repository `Baumus/centsys_remote_verified`. Never install two providers of the same domain or leave upstream automatic updates enabled for the candidate. If HACS reports an existing provider, resolve the source conflict before downloading; do not overwrite manually to bypass it.
4. Enable pre-release versions where required and select `0.6.3b2` explicitly. Record the exact commit and package checksum. Restart HA only at the agreed installation window. Verify the loaded version and unchanged entity IDs. Keep **Enable live status** enabled.
5. Discover the new Verified telemetry entity ID from the registry. Do not assume its generated slug. Retain the existing cover/operator status IDs. Apply the separately prepared dashboard only after mapping and acceptance.
6. Initially compare only the physically/app-verified open state; no motor command is required for that test. Movement tests need an explicit supervised release from the owner.

## Rollback

Restore the previous repository/source and exact recorded version through HACS, then restart in a safe window. If source switching fails, restore the verified HA backup. Do not remove config entries or entity-registry records. Recheck IDs. The old version can falsely show closed, so do not treat reverting as restored positional reliability. Remove or clearly label the preview-only Verified telemetry tile after rollback.

## Publication

Proposed fork: `Baumus/centsys_remote_verified`, public, tag `v0.6.3b2`, marked pre-release. Publish only reviewed code, MIT license, sanitized tests/docs and standard icons; no property identifiers, private diagnostics, access details or owner-specific dashboards. Publication and an upstream PR are separate external actions; this local preparation does neither.
