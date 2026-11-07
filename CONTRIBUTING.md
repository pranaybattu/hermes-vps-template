# Contributing

1. Create a virtual environment and install the project with `pip install -e .`.
2. Run `hermes-infra validate --config hermes-infra.toml` against a local
   non-secret profile, and `python -m compileall src` before opening a PR.
3. Do not include real host identifiers, credentials, Terraform state, or
   screenshots containing secret values in commits or issues.
4. Keep changes small, explain operational impact, and update the relevant docs.

CI performs syntax compilation and profile validation. Live VPS or tailnet
changes must be reviewed and run by an operator; CI never deploys.

## Before you push
- Run `python -m unittest discover -s tests`; `tests/test_public_safe.py` fails on tailnet IPs/hostnames and emails.
- Run `gitleaks protect --staged --redact`.
- Put your own real org, host and project names in a local, git-ignored `.public-safe-denylist` (one per line) so the test catches them.
