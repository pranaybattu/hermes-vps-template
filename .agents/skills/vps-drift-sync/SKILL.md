---
name: vps-drift-sync
description: Manually inspect VPS Hermes Compose drift and open a PR for safe VPS-side changes. Never deploy or expose environment values.
---

# VPS Compose drift sync

Run only when the operator invokes this skill. It compares safe Compose
configuration from the VPS with this repository and opens a PR for review.

1. Confirm the worktree is clean. Fetch `origin/main` and create a unique branch
   from that ref. Never commit or push to `main`.
2. Read the Compose path from the local, ignored `hermes-infra.toml` profile.
   Do not use `docker compose config`, `docker inspect`, container environment
   output, or logs to collect configuration. If the repository has no canonical
   Compose file yet, run inventory only, show the sanitized candidate for review,
   and stop; do not create or push a PR until the operator has approved a tracked
   Compose source.
3. Create a mode-700 temporary directory outside the repository. Read the raw
   Compose file over SSH and pipe it directly to `scripts/sanitize_compose.py`.
   Do not display, log, save, or send raw input to an agent. The sanitizer drops
   every `environment` and `env_file` key recursively.
4. If SSH or sanitization fails, stop without showing input. Before reading the
   sanitized file, run `gitleaks detect --source <temp-dir> --no-git --redact`.
   A finding or missing scanner stops the workflow.
5. Show only the sanitized diff for operator review. Copy approved non-secret
   changes into the tracked Compose file while preserving its existing
   `environment` and `env_file` sections unchanged. Never copy those sections
   from the VPS. Stage only reviewed changes, then run
   `gitleaks protect --staged --redact` immediately before pushing.
6. Push only the new branch ref and open a PR targeting `main`. Never force-push,
   merge, deploy, or push to `main`.

Delete the temporary directory when finished. If the sanitized configuration
cannot be compared safely, stop and ask the operator to review it locally.
Gitleaks is a backstop; it does not guarantee
that every kind of secret is detected. GitHub cannot enforce the branch rule on
a private repository on some GitHub plans, so repository writers can bypass this
skill.
