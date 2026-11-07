# Security model

- Secret values stay in Hostinger Docker Manager, not in TOML, source code,
  command-line arguments, Terraform files, or CI logs.
- Profiles contain only secret variable names. The manager prints those names
  for setup guidance and does not retrieve container environment values.
- SSH uses the system OpenSSH client in batch mode and honors configured
  `known_hosts`; do not disable host-key checking.
- `deploy` requires an explicit confirmation unless `--yes` is supplied. It
  targets one configured service and does not remove orphan containers or
  volumes.
- Do not commit Terraform state or plan files. Tailscale state can contain
  policy details and credentials.
- Treat Hostinger panel, VPS root, and Docker access as privileged: an operator
  with those permissions may be able to inspect running container settings.
- The manual drift skill excludes complete `environment` and `env_file`
  sections before showing Compose data and requires a redacted Gitleaks scan
  before a branch push. This reduces accidental leaks but cannot guarantee that
  every secret format is detected; review the sanitized diff before opening its
  PR.
- The production workflow uses GitHub environment secrets, ephemeral Tailscale
  access, Tailscale SSH policy checks, and a client-encrypted Restic backup.
  It does not retrieve provider values to the runner or print rendered Compose
  output; Compose validation resolves any needed values quietly on the VPS.
- CI runs Gitleaks against repository history with full redaction. The local
  drift-review skill also scans its proposed branch before pushing.
- The SQLite backup process writes a consistent online snapshot to stdout only
  after an integrity check; the workflow pipes it directly to Restic. Restore
  access still depends on the Restic password and Google Drive OAuth config
  being protected.
- A manual workflow dispatch does not prevent a repository writer from
  changing the workflow. Restrict repository write access and production
  environment access before adding the Restic password or Google Drive OAuth
  config. Private environment required-reviewer rules need GitHub Enterprise;
  the manual dispatch remains the human deployment gate on lower eligible
  plans.

See GitHub's [protected branch plan requirements](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
and [environment protection plan requirements](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

If a provider key is exposed, rotate it in that provider and update the value
in Hostinger. Do not paste the replacement into an issue or commit.
