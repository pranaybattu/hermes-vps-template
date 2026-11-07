---
name: hermes-recover
description: Roll back a bad deploy, restore a Mnemosyne snapshot, or diagnose a restart loop.
---

# hermes-recover

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. Diagnose first, read-only: `docker compose ps -a`, last 40 log lines (redact anything key-like), `ls -ln` on the data volume. Match against `docs/troubleshooting.md`.
2. Rollback an image: open a PR restoring the previous image digest in `docker-compose.yml`, merge after CI, dispatch `hermes-deploy`. The VPS also keeps `.<compose-file>.rollback`.
3. Restore data: restore the restic snapshot to a temp directory, run `PRAGMA integrity_check`, then (with approval and the agent stopped) copy it to the database path and restart.
4. Never delete volumes. Never run `docker compose down -v`.

## Stop if
A step would delete a volume or overwrite data without a verified backup.
