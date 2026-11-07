# Hermes VPS Template

Run your own [Hermes Agent](https://hermes-agent.nousresearch.com) with the Workspace UI and
Mnemosyne memory on a single Ubuntu VPS, managed entirely from code: Docker Compose, a private
Tailscale network, GitHub Actions deploys, and encrypted restic backups. No passwords, tokens
or account details live in this repository.

> **Tested on:** one Hostinger Ubuntu VPS, Tailscale, GitHub Actions, restic over rclone to Google Drive.
> Other Ubuntu VPS providers should work but are untested.

## What you get

- Hermes agent + Workspace UI in Compose, bound to loopback only (no public ports).
- Dashboard served over **tailnet-only HTTPS** (`tailscale serve`, Funnel refused).
- Deploys from GitHub Actions with an ephemeral Tailscale identity, no SSH keys in GitHub.
- A pre-deploy encrypted SQLite backup of the Mnemosyne memory database.
- A small CLI (`hermes-infra`) to validate your profile and run Compose actions over SSH.
- Agent skills that walk you through every step (see below).

## Quick start

1. Use this repo as a template (or clone it) into your **own private** repository. Do not commit real values.
2. Follow [docs/runbook.md](docs/runbook.md), or let a coding agent run the skills in order:
   `hermes-preflight` → `hermes-setup` → `hermes-github-env` → `hermes-backups` →
   `hermes-deploy` → `hermes-verify`. Use `hermes-recover` when something breaks.
3. Local tooling check:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
hermes-infra init        # writes hermes-infra.toml (git-ignored)
hermes-infra validate
```

## Skills

Skills live in `.agents/skills/<name>/SKILL.md`. To use them in Claude Code, copy or symlink
them into `.claude/skills/`. Every skill follows the same rules: it never reads, prints or logs
secret values, takes secrets only through a hidden prompt or stdin, and asks before any change
on your VPS, GitHub or Tailscale account.

| Skill | Purpose |
|---|---|
| `hermes-preflight` | Read-only check of local tools, GitHub login and VPS reachability |
| `hermes-setup` | Profile, Tailscale policy and workload identity |
| `hermes-github-env` | `production` environment, variables and secrets |
| `hermes-backups` | rclone remote, restic repository, restore drill |
| `hermes-deploy` | Dispatch and watch the deploy, read failures |
| `hermes-verify` | Private dashboard, memory status, no public exposure |
| `hermes-recover` | Roll back, restore, diagnose restart loops |
| `vps-drift-sync` | Compare the VPS Compose file with the repo (sanitized) |

## Security model

Secrets stay on the VPS or in GitHub environment secrets. Profiles hold variable **names** only.
CI scans history with Gitleaks and a test fails if real-looking IPs, tailnet hostnames or emails
are committed. Read [docs/security.md](docs/security.md) and [SECURITY.md](SECURITY.md).
**Restrict who can run workflows and edit this repo:** a deploy runs commands as root on your VPS.

## Docs

[Runbook](docs/runbook.md) · [VPS setup](docs/vps-setup.md) · [Tailscale](docs/tailscale.md) ·
[Mnemosyne](docs/mnemosyne.md) · [Configuration](docs/configuration.md) ·
[Troubleshooting](docs/troubleshooting.md)

## Repository map

| Path | Purpose |
|---|---|
| `src/hermes_infra_manager/` | CLI, profile validation, SSH/Compose operations |
| `docker-compose.yml`, `Dockerfile.workspace` | Reviewed Compose source with variable references only |
| `infra/tailscale/` | Tailscale policy and Terraform |
| `.github/workflows/` | CI and manually dispatched deploy |
| `scripts/` | Memory install, SQLite snapshot, dashboard auth and private HTTPS helpers |
| `.agents/skills/` | Executable steps for coding agents |

## Contributing and license

MIT. See [CONTRIBUTING.md](CONTRIBUTING.md).
