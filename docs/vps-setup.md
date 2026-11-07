# VPS setup

> **Tested only on a Hostinger Ubuntu VPS.** On another Ubuntu VPS with Docker Compose and
> Tailscale, skip the Hostinger Docker Manager notes and keep secret values in the Compose
> project's `.env` on the server (mode 600), never in Git. The `HOSTINGER_*` variable names
> and the `[hostinger]` profile section are historical; they work for any VPS.

## One-time preparation

1. In Hostinger Docker Manager, record the current Compose project directory,
   Compose filename, and Hermes service name. Keep the existing persistent
   Hermes data volume.
2. Confirm Tailscale SSH works from your trusted workstation. The GitHub
   deployment workflow uses Tailscale SSH and does not need an OpenSSH key.
3. Create a profile with `hermes-infra init`; set the SSH and Compose fields and
   change `profile.example` to `false` only after replacing the placeholders.
4. In Hostinger Docker Manager, open the Hermes project's **Environment
   variables** section and paste provider keys there. Add only the variable
   names to `[hostinger].required_environment` in the profile.
5. Keep variable references in the Compose YAML, for example
   `${ANTHROPIC_API_KEY:-}`. Do not paste real keys into the YAML editor or repo.
6. Run `hermes-infra validate`, review `hermes-infra plan`, then use `status`
   before the first deploy.

## Routine deployment

`hermes-infra deploy` runs `docker compose config --quiet`, `pull`, `up -d`, and
`ps` remotely for the configured service. It does not alter Hostinger's
environment-variable settings or print the rendered Compose model.

Use Hostinger's environment-variable UI when rotating or adding API keys. Save
and deploy through Docker Manager so the host-managed values remain the source
of truth. Then run the manager's `status` command.

## Manual drift review

Invoke `.agents/skills/vps-drift-sync/SKILL.md` when you want to compare
the deployed Compose source with the repository. It omits all `environment`
and `env_file` sections, requires Gitleaks, and creates a PR from a new branch
off `origin/main`. Review the sanitized diff before merging. The skill never
deploys or pushes directly to `main`.

## GitHub Actions deployment

The `Deploy to VPS` workflow can only run from `main`. Start it manually
after CI passes; this separate workflow dispatch is the human approval to
deploy that exact commit. It checks for a successful `CI` push run for the same
SHA, validates Compose quietly, backs up Mnemosyne, then copies the reviewed
tracked Compose file to the VPS and recreates `hermes-agent` and `hermes-workspace` together. It requires
an immutable image digest and never copies `.env` or prints Hostinger environment
values. Compose validation runs quietly on the VPS; provider values are not
retrieved by the runner or sent to GitHub.

Create a GitHub environment named `production` and add these environment
variables. Copy the project path and Compose filename from Docker Manager; the
workflow deliberately has no guessed defaults.

| Variable | Value |
|---|---|
| `HOSTINGER_HOST` | VPS Tailscale IP or DNS name |
| `HOSTINGER_USER` | SSH account |
| `HOSTINGER_PROJECT_DIR` | Existing Hostinger Compose project directory |
| `COMPOSE_FILE` | Tracked Compose filename at the repository root and VPS project root |
| `HERMES_SERVICE` | `hermes-agent` |
| `MNEMOSYNE_DB_PATH` | `/opt/data/mnemosyne/data/mnemosyne.db` |

Add these **environment secrets** to `production`:

| Secret | Contents |
|---|---|
| `TS_OAUTH_CLIENT_ID` | Tailscale workload identity client ID |
| `TS_AUDIENCE` | Tailscale workload identity audience |
| `RESTIC_PASSWORD` | Strong Restic repository encryption password |
| `RCLONE_CONFIG_B64` | Base64-encoded rclone config for the Google Drive remote |

The Tailscale runner uses the existing `tag:ci` workload identity and an
ephemeral node. Configure the VPS as `tag:hermes-vps`, then allow `tag:ci` to
use Tailscale SSH as `root` on that tag with `action: accept`. Preserve human
access with a separate checked rule (`action: check`) from tailnet members to
the VPS. Keep all existing policy rules; review the full policy before applying
changes. This removes the OpenSSH private-key and `known_hosts` secrets. Do not
use `ssh-keyscan` for Tailscale SSH.

The workflow dispatch is a manual deployment gate. GitHub does not provide
required environment reviewers for private repositories on every plan, so
review who can dispatch workflows and edit this repository before adding
production secrets.

### Encrypted Mnemosyne backup

Only `mnemosyne.db` is backed up. `scripts/sqlite_snapshot.py` uses SQLite's
online backup API and streams the integrity-checked snapshot directly to
Restic, so the runner does not create a plaintext database file. Restic encrypts
the backup before rclone sends it to `drive:hermes-production/mnemosyne`.
Initialize that repository once from a trusted workstation after configuring
the same rclone remote and Restic password. Keep both credentials in a password
manager and GitHub's `production` environment; do not commit either config.

```bash
set -e
export RCLONE_CONFIG="$HOME/.config/rclone/rclone.conf"
export RESTIC_REPOSITORY='rclone:drive:hermes-production/mnemosyne'
read -r -s -p 'Restic password: ' RESTIC_PASSWORD
echo
export RESTIC_PASSWORD
trap 'unset RESTIC_PASSWORD' EXIT
restic init
```

The first installation may have no database yet. Use the workflow's
`bootstrap_without_database` checkbox only for that initial setup. Later runs
stop if the database is absent or the backup cannot be created and read back.
Before relying on backups, perform a separate restore drill to a temporary
directory; the deploy workflow never restores data or performs an automatic
rollback. To roll back an image update, merge a PR restoring the previous image
digest and manually dispatch that deployment; restore the Mnemosyne snapshot
separately only if the database itself needs recovery.

Create the environment secrets without displaying their values in the shell.
For example, pipe a local rclone config directly into GitHub CLI:

```sh
base64 < "$HOME/.config/rclone/rclone.conf" | tr -d '\n' \
  | gh secret set RCLONE_CONFIG_B64 --env production
```

Use `gh secret set NAME --env production` for interactive secrets, or pipe a
file to `gh secret set NAME --env production`. Never put secrets in workflow
inputs, vars, shell command arguments, or repository files.

### Mnemosyne setup

The deploy workflow runs `scripts/install_mnemosyne.sh` inside the Hermes
container after updating it. The script uses the Hermes Python interpreter,
keeps the pinned Mnemosyne wrapper in the persistent `/opt/data` mount, selects
the provider, and checks memory status. It stops if the Python minor version
changed and the existing side environment needs review. This keeps Mnemosyne
inside Hermes as a plugin; it does not add a network service or expose a port.

## Current boundary

Before the first deployment, invoke the manual drift skill to inventory the
existing Compose project and review a sanitized candidate. The workflow refuses
to run until a reviewed Compose file exists in the repository root. It validates
a temporary copy, takes the database backup, then atomically replaces the
tracked Compose file on the VPS. Hostinger's `.env` and other files remain in
place. Preserve all current services and volume declarations in the reviewed
file; do not dispatch deployment before that review.

## Private dashboard rollout

The dashboard is enabled explicitly on container port 19119 and published only
on VPS loopback port 9119. Public Traefik labels are removed. After a successful
rollout, `scripts/private_dashboard.sh` checks HTTP health and configures Tailscale
Serve on HTTPS port 443. It refuses to proceed if Funnel is enabled. Do not enable
Funnel: that would make the service public. The CI tag retains SSH-only access;
human member devices use the existing tailnet grants for HTTPS.

Before deploying, set these three values in the VPS project's environment UI.
Use a password manager to generate and retain the secrets; do not paste them into
Git, PRs, workflow inputs, or this chat:

- `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`: your chosen dashboard login name.
- `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`: a unique password of at least 24 characters.
- `HERMES_DASHBOARD_BASIC_AUTH_SECRET`: a separate random session signing secret
  of at least 32 characters. Keep it stable across restarts.

Keep `HERMES_DASHBOARD_PUBLIC_URL` set to the VPS's full Tailscale HTTPS URL.
The Compose file fails validation when the three authentication values are
absent. The dashboard binds to the container interface, so its auth provider is
required even though the Docker host port is loopback-only.

The initial limits for the 2-vCPU/8-GiB VPS are 1 CPU and 4 GiB for Hermes and
0.35 CPU and 1 GiB for Workspace, with bounded logs and process counts. These are
conservative starting caps, not measured optimal values. They leave headroom for
Docker and Tailscale. Measure CPU at idle and during one representative task;
limits do not cure restart loops or remove Hostinger's hypervisor throttling.

The official Hermes dashboard supports profiles and sessions, so multiple
projects alone do not require the separate third-party Workspace service.
Workspace is retained for the existing file-management workflow and its volume;
it is not published through Serve. Both containers are recreated together because
Workspace shares the agent's network namespace. The current workflow uses the
already-built Workspace image and does not yet build that image in CI.

### Laptop and phone acceptance checks

1. Sign in to Tailscale on both devices using an allowed human member account.
2. Connect Tailscale, open the VPS HTTPS name shown by `tailscale serve status`,
   and sign in with the dashboard credentials above.
3. Verify the dashboard loads and send a harmless message using the configured
   model provider. Provider secrets remain on the VPS.
4. Disconnect Tailscale on the phone and confirm the same URL is unreachable.
5. Reconnect and confirm access returns. Do not expose public ports to fix DNS.

### Deployment and rollback evidence

Merge the reviewed PR after CI passes, then separately approve deployment by
manually dispatching `Deploy to VPS` for that main commit. The workflow
checks the exact main SHA, validates Compose, snapshots Mnemosyne, recreates both
services, installs the memory plugin, and checks dashboard health. Bootstrap can
skip only an explicit missing-file result; an SSH or container failure still
stops rollout. First-install bootstrap is not permission to skip configured
backup credentials or a database that already exists.

A server-local mode-600 Compose copy is retained as `.docker-compose.yml.rollback`.
It is never uploaded or read into Git; it may contain old server-side values.
Roll back through a new PR reverting the deployment configuration, then manually
dispatch it after CI. There is no automatic data restore. A failed rollout can
leave services unavailable until the operator rolls back; restoring Compose
alone does not undo memory plugin changes in the persistent volume.

Before claiming end-to-end completion, validate an encrypted backup and restore
it into a temporary location, check SQLite integrity, and remove the temporary
restore. Google OAuth must be in production and the rclone remote reauthorized
before relying on it for unattended backups. The current deployment workflow
backs up only before rollout; scheduled backups are not configured.

Configuration changes belong in reviewed branches and PRs. Manually invoke the
drift-sync skill for VPS changes; automatic collection of all Hermes files is
unsafe because config files can contain secrets. Only reviewed non-secret
settings should be adopted. Runtime conversations and credentials are not Git
configuration.

Alternatively, run the reviewed `scripts/configure_dashboard_auth.py` interactively
on the VPS with the existing project's `.env` path as its argument. It prompts
for a password twice, configures username `admin`, generates the session key,
appends settings without reading existing values, and restricts the file to mode
600. Re-running rotates the session key and invalidates existing sessions.
The file must already exist. Keep the chosen password in your password manager.
Do not subsequently overwrite that file from an outdated Docker Manager editor.

`docs/oauth-branding/` contains proposed public homepage and privacy text for the
personal backup integration. These files are drafts until the operator approves
publication and confirms the described data handling. Do not publish this private
repository. A separate minimal public GitHub Pages site can be used; verify its
ownership in Google Search Console and register its domain in Google OAuth.

### Shared-volume runtime ownership

The current Workspace image runs its Node process as UID 10010. Hermes explicitly
uses the same UID because both services share owner-only state files. A default
UID 10000 agent cannot open existing UID 10010 install locks. Changing this UID
requires reviewing the ownership of both services' persistent files.

Deployment waits for dashboard TCP readiness before memory setup. The installer
and memory status command run as the container `hermes` user; the installer
refuses root to prevent new root-owned runtime files. A failed earlier root
installation can leave `/opt/data/venvs/mnemosyne` and `/opt/data/mnemosyne` owned
by root. Repair only those managed trees and the `venvs` directory's owner to
UID 10010/GID 10000, without following symlinks or reading file contents, before
retrying. Preserve all data. This repair is needed only for that failed attempt.
