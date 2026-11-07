# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `hermes-agent` restarts; log says `install state is not writable` | Agent UID differs from the owner of existing files (Workspace runs as 10010) | Keep `HERMES_UID: "10010"` in Compose, redeploy |
| Deploy stops at the backup step with "container is restarting" | The DB check cannot run in a crash-looping container | Dispatch with `bootstrap_without_database` checked; fix the restart cause |
| Install step fails with `No module named pip` | A venv from an interrupted run lacks pip | The installer runs `ensurepip`; redeploy |
| Tailscale OIDC exchange returns 403 | Subject mismatch (GitHub includes immutable IDs) | Copy the received subject from the diagnostic; never use `*` |
| Dashboard password script rejects the password | `$` is interpolated by Compose | Use 24+ ASCII characters without `$` |
| Backups fail after about 7 days | Google OAuth app still in Testing mode | Publish the app, then `rclone config reconnect drive:` |
| Deploy fails with an image error for Workspace | The local Workspace image was never built on the VPS | Build `Dockerfile.workspace` on the VPS, pinned by digest |
