---
name: hermes-preflight
description: Read-only check that this machine and accounts are ready to set up Hermes on a VPS. Use before any other hermes skill.
---

# hermes-preflight

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. Check tools exist: `python3 --version` (3.11+), `gh`, `ssh`, `tailscale`, `terraform`, `restic`, `rclone`, `gitleaks`. List the missing ones with install hints; do not install without approval.
2. `gh auth status` must show a logged-in account. Note which account and ask if it is the intended owner.
3. Confirm `hermes-infra.toml` exists and `hermes-infra validate` passes (run `hermes-infra init` only with approval).
4. Check the VPS answers over Tailscale: `tailscale status` lists it, then `tailscale ssh <user>@<host> true`. If Tailscale asks for a browser identity check, tell the user to approve it and reply done.
5. Report a pass/fail table.

## Stop if
A required tool is missing, `gh` is not logged in, or the VPS is unreachable.
