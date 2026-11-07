# Runbook

Every step ends with a **Checkpoint**. Do not continue until it passes. Replace `<PLACEHOLDERS>`
with your own values. Never paste secrets into chat, issues or command-line arguments.

## 0. Prerequisites
- An Ubuntu VPS you control with Docker + Compose, and a Tailscale account with the VPS joined (tag it `tag:hermes-vps`).
- Local: Python 3.11+, `gh` (logged in), `tailscale`, `terraform`, `restic`, `rclone`, `gitleaks`, OpenSSH.
- Your own **private** GitHub repo created from this template.

Checkpoint: `gh auth status` succeeds and `tailscale ssh root@<VPS_TAILNET_NAME> true` works.

## 1. Create your deployment
Copy the example: `cp -r deployments/example deployments/<DEPLOYMENT>` (lowercase letters, digits, dashes). Each deployment has its own Compose file, GitHub environment, Tailscale identity and backup repository, so deployments never share secrets or data.

## 1b. Profile
```sh
pip install -e . && hermes-infra init --output deployments/<DEPLOYMENT>/hermes-infra.toml
```
Edit `deployments/<DEPLOYMENT>/hermes-infra.toml` (git-ignored): host, user, Compose project directory, service. Set `profile.example = false`.

Checkpoint: `hermes-infra validate --config deployments/<DEPLOYMENT>/hermes-infra.toml && hermes-infra plan --config deployments/<DEPLOYMENT>/hermes-infra.toml` print your values and no secrets.

## 2. Tailscale policy and CI identity
1. Review `infra/tailscale/policy.hujson`, then `terraform -chdir=infra/tailscale plan` and apply only after reading it.
2. In the Tailscale admin console create a GitHub Actions workload identity: scope `auth_keys`, tag `tag:ci`,
   subject `repo:<ORG>@<ORG_ID>/<REPO>@<REPO_ID>:environment:<DEPLOYMENT>`. If the first exchange returns 403, copy the
   *received* subject from the diagnostic, do not widen it to `*`.

Checkpoint: policy tests pass in `terraform plan`; the identity shows your repo's subject.

## 3. GitHub environment
Create environment `<DEPLOYMENT>` (same name as the folder in `deployments/`), restrict it to `main`, and add required reviewers if your plan allows.
Variables: `HOSTINGER_HOST`, `HOSTINGER_USER`, `HOSTINGER_PROJECT_DIR`, `COMPOSE_FILE`, `HERMES_SERVICE`,
`MNEMOSYNE_DB_PATH` (see [vps-setup](vps-setup.md)). Secrets are set from stdin:
```sh
gh secret set TS_OAUTH_CLIENT_ID --env <DEPLOYMENT>
gh secret set TS_AUDIENCE --env <DEPLOYMENT>
gh secret set RESTIC_PASSWORD --env <DEPLOYMENT>
base64 < "$HOME/.config/rclone/rclone.conf" | tr -d '\n' | gh secret set RCLONE_CONFIG_B64 --env <DEPLOYMENT>
```
Checkpoint: `gh secret list --env <DEPLOYMENT>` shows four names (never values).

## 4. Backups
Configure an rclone remote named `drive` (Google Drive; **publish the OAuth app to production**, otherwise
tokens expire after 7 days). Create a restic password in your password manager, then `restic init` as shown in
[vps-setup](vps-setup.md#encrypted-mnemosyne-backup). Keep the password: without it backups are unreadable.

Checkpoint: `restic snapshots` runs; do a restore drill into a temp directory once there is data.

## 5. Dashboard password (on the VPS)
```sh
ssh -t root@<VPS_TAILNET_NAME> 'python3 /root/hermes-configure-dashboard-auth.py <PROJECT_DIR>/.env'
```
(copy `scripts/configure_dashboard_auth.py` there first). Choose 24+ ASCII characters without `$`; input is hidden.

Checkpoint: the script prints "login admin configured" and never echoes the password.

## 6. First deploy
Merge to `main`, wait for CI, then run **Actions → Deploy to VPS** with `deployment=<DEPLOYMENT>` and `bootstrap_without_database` checked
(first install only). Later deploys leave it unchecked.

Checkpoint: the workflow finishes green; `docker compose ps` on the VPS shows both services `healthy`.

## 7. Verify
- Open `https://<VPS_TAILNET_NAME>` from a device on your tailnet and sign in.
- From a device **off** the tailnet the same address and the VPS public IP on ports 9119/32770 must fail.
- `docker compose exec -T --user hermes hermes-agent hermes memory status` shows provider `mnemosyne`.

## 8. Recover
Bad image: merge a PR restoring the previous image digest and re-dispatch. Bad data: restore the restic
snapshot to a temp path, check it with SQLite `PRAGMA integrity_check`, then copy it into place with the agent stopped.
