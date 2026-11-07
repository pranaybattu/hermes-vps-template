"""Build and run safe SSH commands for the existing remote Compose project."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Sequence

from .config import Profile


def ssh_command(profile: Profile, compose_action: str) -> list[str]:
    """Build an SSH argv that operates only on the configured Compose service."""
    compose = [
        "docker",
        "compose",
        "--project-directory",
        profile.project_directory,
        "-f",
        profile.compose_file,
    ]
    remote_parts = [
        f"cd {shlex.quote(profile.project_directory)}",
        " && ",
        shlex.join(compose),
        " ",
        compose_action,
    ]
    # `compose config` accepts no service positional argument; runtime actions do.
    if compose_action != "config --quiet":
        remote_parts.extend([" ", shlex.quote(profile.service)])
    remote_command = "".join(remote_parts)
    target = f"{profile.user}@{profile.host}"
    command = ["ssh", "-o", "BatchMode=yes"]
    if str(profile.identity_file):
        command.extend(["-i", str(profile.identity_file)])
    command.extend([target, remote_command])
    return command


def run_command(command: Sequence[str]) -> int:
    """Run a command directly so output and failures remain visible to the user."""
    print("$ " + shlex.join(command))
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        executable = command[0] if command else "command"
        print(f"Required executable not found: {executable}")
        return 127
    return result.returncode


def remote_action(profile: Profile, action: str) -> int:
    """Run a fixed Compose action; only the configured service is targeted."""
    allowed = {"config --quiet", "pull", "up -d", "ps"}
    if action not in allowed:
        raise ValueError(f"Unsupported Compose action: {action}")
    return run_command(ssh_command(profile, action))
