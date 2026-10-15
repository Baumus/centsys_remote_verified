# Security policy

This is an unofficial, experimental integration that can control physical equipment. No security response time or hardware safety certification is promised.

## Supported versions

Security fixes target the current development branch and the newest published pre-release. Older pre-releases are not maintained separately. Use the release notes to assess upgrade and rollback implications; a successful CI run is not a live-device safety assessment.

## Report a vulnerability privately

Use GitHub's [Report a vulnerability](https://github.com/Baumus/centsys_remote_verified/security/advisories/new) for this repository. Do not open a public issue or pull request containing an exploit, credentials, access data or identifying device/property information. If the private reporting option is temporarily unavailable, do not publish sensitive details; wait until the private route is available.

Describe affected versions, impact, and a minimal reproduction using synthetic data. Do not test against someone else's device or account, bypass access controls, or trigger physical movement to demonstrate a vulnerability. Share only the minimum redacted evidence necessary. Coordinate disclosure with the maintainer after a fix is available.

## Public logs and diagnostics

Review every log, screenshot and fixture before sharing. Remove phone numbers, PINs, tokens, account/device identifiers, certificates containing private material, location and network/access details. Never attach Home Assistant `.storage`, backups, private keys or raw account/API responses. Do not assume debug logs are safe merely because they came from this integration.
