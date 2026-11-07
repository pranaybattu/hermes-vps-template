# Security policy

## Reporting
Open a private security advisory on this repository (Security → Report a vulnerability).
Do not post exploit details, hostnames, tokens or logs in public issues.

## What counts as a leak
Passwords, API keys, OAuth tokens, rclone or restic config, Terraform state, Tailscale auth keys,
private IPs or tailnet names tied to a real deployment, personal emails, and screenshots showing them.

## If you leaked something
1. **Rotate first** at the provider (Tailscale, Google, GitHub, model APIs). Deleting a commit is not enough.
2. Remove it from the repository history only after rotating.
3. Re-run `gitleaks detect --redact` and the test suite.

## Scope
This project deploys software as root on a server you own. Review every change to
`.github/workflows/`, `docker-compose.yml` and `scripts/` before merging.
