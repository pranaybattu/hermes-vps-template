"""Test the private routing gate without contacting any network service."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/private_dashboard.sh'


class PrivateDashboardTests(unittest.TestCase):
    def run_probe(self, code, config):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in {
                'tailscale': '#!/bin/sh\nif [ "$2" = status ]; then printf "%s" "$SERVE_CONFIG"; else touch "$MARKER"; fi\n',
                'curl': '#!/bin/sh\nprintf "%s" "$HTTP_CODE"\n',
                'sleep': '#!/bin/sh\nexit 0\n',
            }.items():
                tool = root / name
                tool.write_text(body)
                tool.chmod(0o700)
            (root / 'python3').symlink_to(sys.executable)
            marker = root / 'published'
            result = subprocess.run(['sh', str(SCRIPT)], capture_output=True, timeout=10,
                env={'PATH': directory + ':/usr/bin:/bin', 'SERVE_CONFIG': config,
                     'HTTP_CODE': str(code), 'MARKER': str(marker)})
            return result.returncode, marker.exists()

    def test_login_redirect_can_be_published(self):
        self.assertEqual(self.run_probe(302, '{}'), (0, True))

    def test_unhealthy_dashboard_is_not_published(self):
        status, published = self.run_probe(500, '{}')
        self.assertNotEqual(status, 0)
        self.assertFalse(published)

    def test_funnel_and_unreadable_config_fail_closed(self):
        for config in (json.dumps({'AllowFunnel': {'fixture.invalid:443': True}}), 'invalid'):
            status, published = self.run_probe(200, config)
            self.assertNotEqual(status, 0)
            self.assertFalse(published)
