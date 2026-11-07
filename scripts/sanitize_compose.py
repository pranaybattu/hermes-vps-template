"""Remove Compose environment sections before configuration reaches an agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject ambiguous mappings instead of silently keeping the last key."""


def _unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError("duplicate YAML key")
        mapping[key] = loader.construct_object(value_node)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)


def sanitize(value: object) -> object:
    """Return a parsed Compose document without environment values or file refs."""
    if isinstance(value, dict):
        return {
            key: sanitize(item)
            for key, item in value.items()
            if key not in {"environment", "env_file"}
        }
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        document = yaml.load(sys.stdin, Loader=UniqueKeyLoader)
        if not isinstance(document, dict):
            raise ValueError("Compose document must be a mapping")
        with args.output.open("x", encoding="utf-8") as output:
            yaml.safe_dump(sanitize(document), output, sort_keys=True)
    except (yaml.YAMLError, OSError, RecursionError, TypeError, ValueError):
        print("Could not safely sanitize Compose input; stopped.", file=sys.stderr)
        return 2
    print("Sanitized Compose file written; environment sections omitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
