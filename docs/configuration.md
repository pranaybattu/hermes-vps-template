# Configuration

`hermes-infra.toml` contains non-secret settings for one target profile. Create
it with `hermes-infra init`; the starter template includes comments for every
section. The default file is ignored by Git because hostnames and paths are
operator-specific.

| Section | Fields | Meaning |
|---|---|---|
| `[profile]` | `name`, `example` | Profile label and deployment safety latch |
| `[ssh]` | `host`, `user`, `identity_file` | OpenSSH destination and private-key path |
| `[compose]` | `project_directory`, `file`, `service` | Existing remote Compose project and service to operate |
| `[hostinger]` | `required_environment` | Names to configure in Hostinger; no values are stored here |
| `[tailscale]` | `terraform_directory` | Location reserved for reviewed Terraform policy configuration |

`validate` reads and displays only the non-secret profile fields. `plan` prints
the remote actions. Neither command opens an SSH connection. `status` checks
the Compose project. `deploy` validates the Compose model quietly, then pulls
and recreates the single configured service after confirmation.

Use one profile per target by passing `--config path/to/profile.toml`.
