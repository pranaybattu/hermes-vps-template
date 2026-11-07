---
name: hermes-verify
description: Verify the deployed Hermes is healthy, private and using Mnemosyne memory.
---

# hermes-verify

## Rules for every step
- Never read, print, log, echo or paste secret values (passwords, tokens, rclone/restic config, `.env`). Show names only.
- Secrets enter only through a hidden interactive prompt run by the user, or stdin to `gh secret set`. Never ask the user to paste a secret into chat.
- Use placeholders from the user's own `hermes-infra.toml`; never invent hostnames, IPs or account names.
- Ask for a clear yes before any change on the VPS, GitHub, Tailscale or Google account. Read-only checks need no approval.
- Stop and report at the first failed checkpoint. Do not work around a denial.

## Steps
1. Read-only on the VPS: `docker compose ps` shows both services healthy; `ss -ltn` shows 9119 and 32770 on 127.0.0.1 only.
2. `tailscale serve status` shows tailnet-only HTTPS and no Funnel.
3. `hermes memory status` (as user `hermes`) shows provider `mnemosyne`.
4. Ask the user to open the tailnet URL on a laptop and phone, sign in as `admin`, and send one message. Then, **off the tailnet**, confirm the URL and the public IP on 9119/32770 do not respond.
5. Report what was checked and what the user must still do themselves.

## Stop if
Any port is bound to a non-loopback address, or Funnel is on.
