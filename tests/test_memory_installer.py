"""Prevent root maintenance commands from creating inaccessible runtime state."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/install_mnemosyne.sh'


class MemoryInstallerTests(unittest.TestCase):
    def test_root_is_rejected_before_runtime_or_filesystem_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_id = Path(directory) / 'id'
            fake_id.write_text('#!/bin/sh\nprintf "0\\n"\n')
            fake_id.chmod(0o700)
            result = subprocess.run(['/bin/sh', str(SCRIPT)], capture_output=True,
                                    env={'PATH': directory}, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'Run this installer as the container hermes user', result.stderr)
            self.assertEqual(result.stdout, b'')
