---
name: hermes-deploy
description: Dispatch and watch the GitHub Actions deploy to the VPS, and diagnose failures from logs.
---

# hermes-deploy

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. Confirm CI passed on the exact `main` commit: `gh run list --workflow ci.yml --commit <sha>`.
2. Ask for explicit approval, stating whether `bootstrap_without_database` is true (first install only).
3. `gh workflow run deploy.yml --ref main -f deployment=<DEPLOYMENT> -f bootstrap_without_database=<true|false>`, then `gh run watch <id> --exit-status`.
4. On failure read `gh run view <id> --log-failed`. Check `docs/troubleshooting.md` first. Do not retry blindly.
5. After success run `hermes-verify`.

## Stop if
CI is red for that commit, or the user has not approved the deploy.
