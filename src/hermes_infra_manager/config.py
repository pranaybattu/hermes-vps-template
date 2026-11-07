"""Read and validate non-secret deployment settings from a TOML profile."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when a profile is missing required settings or is malformed."""


@dataclass(frozen=True)
class Profile:
    """Validated settings needed to contact one Compose project."""

    name: str
    example: bool
    host: str
    user: str
    identity_file: Path
    project_directory: str
    compose_file: str
    service: str
    required_environment: tuple[str, ...]
    terraform_directory: Path


def load_profile(path: Path) -> Profile:
    """Parse a TOML profile and reject missing or unsafe command settings."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Profile not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc

    try:
        raw_profile = data["profile"]
        raw_ssh = data["ssh"]
        raw_compose = data["compose"]
        raw_hostinger = data["hostinger"]
        raw_tailscale = data["tailscale"]
        profile = Profile(
            name=_required_string(raw_profile, "name", "profile"),
            example=bool(raw_profile.get("example", False)),
            host=_required_string(raw_ssh, "host", "ssh"),
            user=_required_string(raw_ssh, "user", "ssh"),
            identity_file=Path(
                _required_string(raw_ssh, "identity_file", "ssh")
            ).expanduser(),
            project_directory=_required_string(
                raw_compose, "project_directory", "compose"
            ),
            compose_file=_required_string(raw_compose, "file", "compose"),
            service=_required_string(raw_compose, "service", "compose"),
            required_environment=tuple(
                _string_list(raw_hostinger, "required_environment", "hostinger")
            ),
            terraform_directory=Path(
                _required_string(
                    raw_tailscale, "terraform_directory", "tailscale"
                )
            ),
        )
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"Missing or invalid profile section: {exc}") from exc

    if not profile.host or any(char.isspace() for char in profile.host):
        raise ConfigError("ssh.host must be a hostname or IP without spaces")
    if not profile.user or any(char.isspace() for char in profile.user):
        raise ConfigError("ssh.user must not contain spaces")
    if not profile.project_directory.startswith("/"):
        raise ConfigError("compose.project_directory must be an absolute VPS path")
    if "/" in profile.service or not profile.service:
        raise ConfigError("compose.service must be a Compose service name")
    return profile


def _required_string(section: dict, key: str, section_name: str) -> str:
    """Return a non-empty string setting or explain which field is invalid."""
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"[{section_name}].{key} must be a non-empty string")
    return value.strip()


def _string_list(section: dict, key: str, section_name: str) -> list[str]:
    """Read a TOML string array used for required variable names."""
    values = section.get(key, [])
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise ConfigError(f"[{section_name}].{key} must be an array of strings")
    return values
