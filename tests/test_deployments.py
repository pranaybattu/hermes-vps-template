"""Every deployment folder must be isolated, validly named and pin its Hermes image."""
import re
import unittest
from pathlib import Path

DEPLOYMENTS = Path(__file__).resolve().parents[1] / 'deployments'


class DeploymentLayoutTests(unittest.TestCase):
    def test_each_deployment_is_valid_and_pinned(self):
        folders = [d for d in DEPLOYMENTS.iterdir() if d.is_dir()]
        self.assertTrue(folders, 'at least the example deployment must exist')
        for folder in folders:
            with self.subTest(deployment=folder.name):
                self.assertRegex(folder.name, r'^[a-z0-9][a-z0-9-]{0,30}$')
                compose = (folder / 'docker-compose.yml').read_text()
                self.assertRegex(compose, r'image: nousresearch/hermes-agent@sha256:[a-f0-9]{64}')


if __name__ == '__main__':
    unittest.main()
