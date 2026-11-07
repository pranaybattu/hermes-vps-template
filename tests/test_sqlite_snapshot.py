"""Security checks for the Mnemosyne backup stream."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "sqlite_snapshot.py"


class SQLiteSnapshotTests(unittest.TestCase):
    """Check that backup output is valid and failures expose no database data."""

    def test_stream_is_a_consistent_sqlite_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "memory.db"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE memories (content TEXT)")
                connection.execute("INSERT INTO memories VALUES (?)", ("private fixture",))

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(database)],
                check=False,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(":memory:") as snapshot:
                snapshot.deserialize(result.stdout)
                self.assertEqual(
                    snapshot.execute("SELECT content FROM memories").fetchone(),
                    ("private fixture",),
                )

    def test_missing_database_writes_no_snapshot_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.db"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(missing)],
                check=False,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertNotIn(str(missing).encode(), result.stderr)


if __name__ == "__main__":
    unittest.main()
