"""User-facing command parser and workflows for Hermes infrastructure."""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

from .config import ConfigError, Profile, load_profile
from .operations import remote_action


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser and its documented subcommands."""
    parser = argparse.ArgumentParser(
        prog="hermes-infra",
        description="Validate and operate a Hermes Docker Compose project over SSH.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="write a starter TOML profile")
    init_parser.add_argument("--output", type=Path, default=Path("hermes-infra.toml"))

    for name, help_text in (
        ("validate", "validate a profile without connecting to the VPS"),
        ("plan", "show the planned remote operations without changing anything"),
        ("status", "show the configured Compose service status"),
        ("deploy", "pull and recreate the configured Compose service"),
    ):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.add_argument(
            "--config", type=Path, default=Path("hermes-infra.toml")
        )
        if name == "deploy":
            command_parser.add_argument(
                "--yes", action="store_true", help="skip the interactive confirmation"
            )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one CLI command and convert expected errors into a concise message."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            return initialize_profile(args.output)
        profile = load_profile(args.config)
        if args.command == "validate":
            return validate_profile(profile)
        if args.command == "plan":
            return show_plan(profile)
        if args.command == "status":
            if _reject_example(profile):
                return 2
            return remote_action(profile, "ps")
        if args.command == "deploy":
            if _reject_example(profile):
                return 2
            return deploy(profile, args.yes)
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 2


def initialize_profile(destination: Path) -> int:
    """Write the packaged starter profile without overwriting an existing file."""
    if destination.exists():
        print(f"Refusing to overwrite existing profile: {destination}", file=sys.stderr)
        return 2
    template = files("hermes_infra_manager").joinpath("templates/hostinger.toml")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Created {destination}. Edit it, then run: hermes-infra validate")
    return 0


def validate_profile(profile: Profile) -> int:
    """Confirm the non-secret settings parse and show only safe identifiers."""
    print(f"Profile: {profile.name}")
    print(f"Target: {profile.user}@{profile.host}")
    print(f"Compose project: {profile.project_directory}/{profile.compose_file}")
    print(f"Service: {profile.service}")
    print("Hostinger environment variable names to configure:")
    for name in profile.required_environment:
        print(f"  - {name}")
    print("Profile syntax is valid. No secrets were read.")
    return 0


def show_plan(profile: Profile) -> int:
    """Describe the exact deployment sequence without contacting the host."""
    print(f"Target: {profile.user}@{profile.host}")
    print(f"Compose project: {profile.project_directory}/{profile.compose_file}")
    print("Planned operations:")
    print("  1. Validate the remote Compose configuration without printing it.")
    print(f"  2. Pull the image for service {profile.service}.")
    print(f"  3. Recreate only service {profile.service}.")
    print("  4. Show service status.")
    print("Secrets remain configured in Hostinger Docker Manager.")
    return 0


def deploy(profile: Profile, assume_yes: bool) -> int:
    """Validate, pull, and recreate one service after explicit confirmation."""
    if remote_action(profile, "config --quiet") != 0:
        print("Remote Compose validation failed; deployment stopped.", file=sys.stderr)
        return 1
    if not assume_yes:
        answer = input(f"Deploy {profile.service} to {profile.host}? [y/N] ")
        if answer.strip().lower() != "y":
            print("Deployment cancelled.")
            return 1
    for action in ("pull", "up -d", "ps"):
        result = remote_action(profile, action)
        if result != 0:
            return result
    return 0


def _reject_example(profile: Profile) -> bool:
    """Prevent status or deployment commands from using the unedited starter."""
    if profile.example:
        print(
            "This is still an example profile. Set profile.example = false "
            "after configuring your target.",
            file=sys.stderr,
        )
        return True
    return False
