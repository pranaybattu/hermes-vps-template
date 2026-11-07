---
name: hermes-github-env
description: Create the GitHub production environment, variables and secrets for the deploy workflow without exposing values.
---

# hermes-github-env

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. Confirm the repo is **private** and owned by the user: `gh repo view --json visibility,nameWithOwner`.
2. With approval create environment `production`; restrict to `main`; add required reviewers if the plan allows. If it does not, tell the user that anyone who can run workflows can deploy as root and that repo write access must be limited.
3. Set variables with `gh variable set NAME --env production` (HOSTINGER_HOST, HOSTINGER_USER, HOSTINGER_PROJECT_DIR, COMPOSE_FILE, HERMES_SERVICE, MNEMOSYNE_DB_PATH) from the user's profile.
4. Secrets: the user runs `gh secret set TS_OAUTH_CLIENT_ID|TS_AUDIENCE|RESTIC_PASSWORD --env production` themselves (hidden prompt) and pipes the base64 rclone config to `RCLONE_CONFIG_B64`.
5. Verify with `gh secret list --env production` and `gh variable list --env production` (names only).

## Stop if
The repository is public, or a secret would have to be typed into chat.
