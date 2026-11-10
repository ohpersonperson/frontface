# Security policy

## Reporting a vulnerability

Please report security vulnerabilities privately, not in a public issue:

- Open a private security advisory at https://github.com/ohpersonperson/frontface/security/advisories/new
- Or open a GitHub issue at https://github.com/ohpersonperson/frontface/issues and mark it clearly as a security report so it can be moved to a private advisory.

Do not include exploit code for a live release in a public issue. A minimal reproduction is welcome in the private advisory.

## Scope

The eight frontface packages (`pressit`, `memdate`, `meminqu`, `fairit`,
`postmo`, `frontface-metacog`, `frontface-flashy`, `frontface-proofit`).
All are stdlib-only with no network access at runtime; the main risks are
in the build/publish pipeline, which is why publishing is gated (see below).

## Publishing gate

Releases are published from `.github/workflows/publish.yml` on `v*` tags,
and the publish job runs under a per-package GitHub environment
(`environment: ${{ matrix.dist }}` in the workflow). The environment
protection rule — a human approval before the PyPI upload runs — must be
enabled in the repository settings (Settings > Environments > each package
environment > Required reviewers). That toggle is the repo owner's step;
until it is enabled, the `environment:` line alone does not pause a run.
A signed, provenanced release is not a reviewed release: no tag should
publish without that approval.
