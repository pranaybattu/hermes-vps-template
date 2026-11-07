"""Ensure interactive secret setup preserves existing values and never prints passwords."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('setup_auth', Path(__file__).parents[1] / 'scripts/configure_dashboard_auth.py')
auth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auth)


class DashboardAuthTests(unittest.TestCase):
    def test_appends_without_disclosing_or_changing_existing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / '.env'
            target.write_text('EXISTING=fixture-only\n')
            password = 'fixture-password-for-testing-only'
            output = io.StringIO()
            with patch.object(auth.sys, 'argv', ['setup', str(target)]), \
                 patch.object(auth.sys.stdin, 'isatty', return_value=True), \
                 patch.object(auth.getpass, 'getpass', side_effect=[password, password]), \
                 contextlib.redirect_stdout(output):
                auth.main()
            self.assertTrue(target.read_text().startswith('EXISTING=fixture-only\n'))
            self.assertIn('HERMES_DASHBOARD_BASIC_AUTH_SECRET=', target.read_text())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(password, output.getvalue())
            self.assertNotIn('fixture-only', output.getvalue())

    def test_rejects_interpolation_before_opening_file(self):
        password = 'fixture-password-with-$interpolation'
        with patch.object(auth.sys, 'argv', ['setup', '/nonexistent/.env']), \
             patch.object(auth.sys.stdin, 'isatty', return_value=True), \
             patch.object(auth.getpass, 'getpass', side_effect=[password, password]), \
             patch.object(auth.os, 'open') as opened:
            with self.assertRaises(SystemExit):
                auth.main()
            opened.assert_not_called()
