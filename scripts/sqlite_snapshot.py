"""Write a consistent SQLite backup to stdout without creating a plaintext file."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote


def main() -> int:
    """Stream an integrity-checked online backup for encrypted remote storage."""
    if len(sys.argv) != 2:
        print("Usage: sqlite_snapshot.py DATABASE_PATH", file=sys.stderr)
        return 2

    database = Path(sys.argv[1])
    if not database.is_file():
        print("SQLite database is missing; backup stopped.", file=sys.stderr)
        return 1

    try:
        source_uri = f"file:{quote(str(database), safe='/')}?mode=ro"
        with sqlite3.connect(source_uri, uri=True) as source:
            with sqlite3.connect(":memory:") as snapshot:
                source.backup(snapshot)
                if snapshot.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    print("SQLite integrity check failed; backup stopped.", file=sys.stderr)
                    return 1
                sys.stdout.buffer.write(snapshot.serialize())
    except (OSError, sqlite3.Error, ValueError):
        print("SQLite snapshot failed; backup stopped.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
