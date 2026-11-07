---
name: hermes-setup
description: Create the hermes-infra profile, review and apply the Tailscale policy, and set up the GitHub workload identity.
---

# hermes-setup

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. `hermes-infra init`, help the user fill the git-ignored profile, set `profile.example = false`, then `hermes-infra validate` and `plan`.
2. Review `infra/tailscale/policy.hujson` with the user: tags `tag:ci` and `tag:hermes-vps`, SSH rules, tests. Run `terraform -chdir=infra/tailscale plan`; show it; apply only after approval. Never commit state files.
3. Guide the user to create the Tailscale workload identity (scope `auth_keys`, tag `tag:ci`, subject `repo:<ORG>@<ORG_ID>/<REPO>@<REPO_ID>:environment:production`). The user keeps the client ID and audience for the next skill.
4. On a 403 later, compare the received subject from Tailscale's diagnostic; never widen the subject to `*`.

## Stop if
The existing live policy has not been reviewed, or `terraform plan` would remove access you did not expect.
