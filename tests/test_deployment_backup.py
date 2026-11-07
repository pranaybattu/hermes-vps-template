"""Exercise the workflow's backup gate with local fake SSH and storage tools."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentBackupTests(unittest.TestCase):
    def run_gate(self, status, bootstrap):
        workflow = (ROOT / '.github/workflows/deploy.yml').read_text()
        step = workflow.split('      - name: Back up Mnemosyne database before rollout\n')[1]
        script = textwrap.dedent(step.split('        run: |\n')[1].split('\n      - name:')[0])
        with tempfile.TemporaryDirectory() as directory:
            for name, body in {
                'tailscale': '''#!/bin/sh
case "$*" in
  *"test -f"*) exit "$DATABASE_STATUS" ;;
  *"python - /data/memory.db"*) cat >/dev/null; printf 'fixture snapshot' ;;
  *"rm -f"*) exit 0 ;;
  *) exit 90 ;;
esac
''',
                'restic': '''#!/bin/sh
case "$1" in
  backup) test "$(cat)" = 'fixture snapshot' ;;
  dump) exit 0 ;;
  *) exit 91 ;;
esac
''',
            }.items():
                tool = Path(directory) / name
                tool.write_text(body)
                tool.chmod(0o700)
            environment = {
                'PATH': directory + os.pathsep + '/usr/bin:/bin',
                'DATABASE_STATUS': str(status),
                'BOOTSTRAP_WITHOUT_DATABASE': str(bootstrap).lower(),
                'HOSTINGER_USER': 'fixture', 'HOSTINGER_HOST': 'fixture.invalid',
                'HOSTINGER_PROJECT_DIR': '/fixture', 'COMPOSE_FILE': 'docker-compose.yml',
                'HERMES_SERVICE': 'hermes-agent', 'MNEMOSYNE_DB_PATH': '/data/memory.db',
            }
            return subprocess.run(['bash', '-c', script], cwd=ROOT, env=environment,
                                  capture_output=True, timeout=10).returncode

    def test_existing_database_is_streamed_with_path(self):
        self.assertEqual(self.run_gate(0, False), 0)

    def test_missing_database_requires_explicit_bootstrap(self):
        self.assertNotEqual(self.run_gate(42, False), 0)
        self.assertEqual(self.run_gate(42, True), 0)

    def test_transport_and_container_failures_cannot_skip_backup(self):
        for status in (1, 125, 255):
            with self.subTest(status=status):
                self.assertNotEqual(self.run_gate(status, True), 0)

    def test_stopped_service_is_treated_as_missing_database(self):
        # A crash-looping container cannot be exec'd into; the check must exit 42, not 1.
        workflow = (ROOT / '.github/workflows/deploy.yml').read_text()
        self.assertLess(workflow.index('ps --status running -q $HERMES_SERVICE | grep -q . || exit 42'),
                        workflow.index("sh -c 'test -f $MNEMOSYNE_DB_PATH"))
