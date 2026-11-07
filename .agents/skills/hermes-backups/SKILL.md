---
name: hermes-backups
description: Set up and test encrypted Mnemosyne backups with restic over rclone, including a restore drill.
---

# hermes-backups

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. The user configures an rclone remote named `drive` locally (`rclone config`). Remind them to **publish the Google OAuth app to production**; Testing-mode tokens expire in 7 days. If no domain is available, use the templates in `docs/oauth-branding/` hosted on GitHub Pages and the user's own support email.
2. The user stores a restic password in their password manager and runs `restic init` (hidden prompt, see `docs/vps-setup.md`).
3. After a first deploy has created data, run a backup test and a restore drill into a temp directory; run `PRAGMA integrity_check` on the restored file; delete the temp directory.
4. Remind the user: losing the restic password means the backups cannot be read.

## Stop if
Restic repo is not initialised, or the drill fails integrity_check.
