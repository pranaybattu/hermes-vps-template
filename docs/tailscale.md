# Tailscale adoption

The existing tailnet is already providing access to the VPS. Preserve that
working path while bringing policy under code control.

For GitHub deployment, the VPS must have `tag:hermes-vps`. Retain a checked
human SSH rule to that tag and add a narrowly scoped CI SSH rule: `tag:ci` may
connect as `root` to `tag:hermes-vps` with `action: accept`. Tailscale SSH uses
its own managed host identity; do not copy an OpenSSH `ssh-keyscan` fingerprint
into GitHub for this connection. Verify that an interactive member login still
works after tagging the VPS, before relying on CI.

The reviewed policy is in `infra/tailscale/policy.hujson` and Terraform loads
that complete file through the official Tailscale provider. It preserves the
existing member network rule and member-to-own SSH rule, adds checked member
SSH to the VPS, and gives `tag:ci` only TCP 22 and non-interactive root SSH to
`tag:hermes-vps`. Policy tests cover the CI network grant and CI SSH rule.
Member access remains configured in policy and should be verified with an
interactive login; the test file contains no personal identity.

The provider resource controls the entire tailnet policy file. Before the first
Terraform plan, import the already-live policy into local state; never plan or
apply this resource against an empty state. Use a dedicated Tailscale OAuth
client for local Terraform with the `policy_file` scope and only its required
dependency scopes. Do not reuse the GitHub CI identity, which is scoped to
creating runner auth keys. Tailscale recommends scoped trust credentials over
fully permitted API keys. Store the OAuth secret in a password manager and
provide it only through local environment variables; keep Terraform state
local. GitHub CI only validates the checked-in JSON policy; it never applies
Terraform. The prompts below use Bash syntax. On macOS, start a Bash subshell
from zsh, then run them from the repository root. Keep it open through plan
review and any approved apply; the exit trap clears the credentials.

```sh
bash
set -e
read -r -p 'Tailscale policy OAuth client ID: ' TAILSCALE_OAUTH_CLIENT_ID
read -r -s -p 'Tailscale policy OAuth client secret: ' TAILSCALE_OAUTH_CLIENT_SECRET
printf '\n'
export TAILSCALE_OAUTH_CLIENT_ID TAILSCALE_OAUTH_CLIENT_SECRET
trap 'unset TAILSCALE_OAUTH_CLIENT_ID TAILSCALE_OAUTH_CLIENT_SECRET' EXIT
terraform -chdir=infra/tailscale init
terraform -chdir=infra/tailscale import tailscale_acl.hermes acl
terraform -chdir=infra/tailscale plan
```

If the plan contains only the expected policy tests, apply in the same Bash
subshell after reviewing it:

```sh
terraform -chdir=infra/tailscale apply
exit
```

## Workload identity per deployment

For isolation give each deployment its own identity (subject ends `environment:<name>`) and, if
deployments share a tailnet, its own VPS tag (for example `tag:hermes-<name>`) with a matching
`tag:ci` grant, so one deployment's CI cannot reach another's VPS.


Each deployment's federated identity uses GitHub issuer
`https://token.actions.githubusercontent.com`, the `auth_keys` scope, and
`tag:ci`. Its exact subject has this shape (replace the placeholders with the IDs GitHub reports for your repository):

```text
repo:<ORG>@<ORG_ID>/<REPO>@<REPO_ID>:environment:<DEPLOYMENT>
```

These are repository/organization identifiers, not credentials. GitHub's emitted
subject includes immutable IDs; the older name-only form does not match. If an
OIDC exchange returns 403, inspect the trust credential's received-subject
diagnostic and compare the exact production claim. Do not widen it to `*` or
change network grants to fix authentication. Client ID and audience values remain
in GitHub environment secrets. The current Terraform module manages ACLs only;
this trust setting is recorded here and administered in the Tailscale console.
