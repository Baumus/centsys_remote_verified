# Contributing

Thanks for helping improve this experimental, unofficial fork. Contributions are welcome via forks and pull requests; public visibility does not grant write or release access. The maintainer is [@Baumus](https://github.com/Baumus). Upstream attribution and the MIT license must be preserved.

## Before you start

- Search existing issues and pull requests. Use the bug report or feature request forms for this fork, not the upstream issue tracker.
- Discuss substantial changes in an issue first. Small documentation fixes can go straight to a pull request.
- Read [SECURITY.md](SECURITY.md) before reporting a security problem. Never put credentials, raw account exports, device identifiers or private property details in an issue, PR, screenshot or test fixture.
- Be respectful and constructive. Focus on reproducible behavior and code, not people. Maintainers may remove abusive or sensitive content.

## Development and offline tests

Fork this repository, clone your fork and create a topic branch from `main`.
Use Python 3.12 for the standalone offline regression suite:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

These tests use fake collaborators; they require neither Home Assistant, cloud credentials nor a connected operator. HACS and Hassfest are separate GitHub Actions checks. Passing offline tests is not hardware validation.

## Pull requests

- Keep changes focused and describe the problem, solution, test results and any remaining uncertainty using the PR template.
- Add a meaningful regression test for behavior changes. Use synthetic, redacted fixtures only.
- Preserve fail-closed command guards: missing, stale, moving or intermediate state must not be promoted to a verified stationary endpoint. Do not send a movement command merely to learn the state.
- Treat any real-device test separately: only the device owner may authorize it, with a clear movement area. Never run live-device tests in CI.
- Do not bump the integration version, move release tags, upload release assets or declare hardware support without coordinating with the maintainer.
- Contributions are licensed under the repository's existing MIT license; no additional CLA is required.

`main` requires a pull request, passing HACS, Hassfest and offline tests, and resolution of review conversations. Only maintainers can merge or release. This is currently a single-maintainer repository, so an independent approving review is not required; CODEOWNERS identifies the responsible maintainer, not a second-person approval guarantee.

Fork workflows require maintainer approval for outside contributors. Approval to run CI is not approval to merge. CI has read-only repository permissions and must not use production secrets or `pull_request_target` to execute contributor code.

## Releases

Only the maintainer publishes releases. Pre-releases remain explicitly experimental; use an explicit release tag in HACS and read the release notes. Do not equate a branch commit or green CI with a hardware-validated release.
