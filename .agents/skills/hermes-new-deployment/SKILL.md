---
name: hermes-new-deployment
description: Add a new isolated deployment (its own folder, GitHub environment, Tailscale identity and backup repository) to this repo.
---

# hermes-new-deployment

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account.
- Stop and report at the first failed checkpoint.

## Steps
1. Ask for a deployment name: lowercase letters, digits and dashes, at most 31 characters (for example `home` or `team-a`). Refuse anything else; it becomes a folder, a GitHub environment name and a backup path.
2. `cp -r deployments/example deployments/<name>`. Review the Compose file with the user; keep the Hermes image pinned by digest.
3. Run `hermes-setup` and `hermes-github-env` for this name only. Each deployment needs its own GitHub environment, Tailscale workload identity (subject ends `environment:<name>`), VPS tag and restic repository (`drive:hermes-<name>/mnemosyne`). Never reuse another deployment's secrets.
4. Run `hermes-backups`, then `hermes-deploy` with `deployment=<name>`, then `hermes-verify`.

## Stop if
The name collides with an existing folder, or a secret or VPS from another deployment would be reused.
