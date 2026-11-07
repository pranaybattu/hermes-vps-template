"""Fail if real-looking identifiers or credentials are committed to this public template."""
import ipaddress
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.terraform', '__pycache__', '.venv', '.egg-info'}
SKIP_FILES = {'.terraform.lock.hcl', 'test_public_safe.py'}
EMAIL_OK = re.compile(r'(noreply|example\.(com|org)|\.invalid)', re.I)
PATTERNS = {
    'tailnet hostname': re.compile(r'\b[\w-]+\.[\w-]+\.ts\.net\b'),
    'GitHub token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}'),
    'private key': re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'long base64 blob': re.compile(r'[A-Za-z0-9+/]{100,}={0,2}'),
}
IPV4 = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


def tracked_files():
    for path in ROOT.rglob('*'):
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts) \
                and path.name not in SKIP_FILES and path.suffix not in {'.png', '.jpg'}:
            yield path


class PublicSafeTests(unittest.TestCase):
    def test_no_identifiers_or_credentials(self):
        denylist = ROOT / '.public-safe-denylist'
        words = [w.strip().lower() for w in denylist.read_text().splitlines() if w.strip()] \
            if denylist.exists() else []
        problems = []
        for path in tracked_files():
            text = path.read_text(errors='ignore')
            rel = path.relative_to(ROOT)
            for label, pattern in PATTERNS.items():
                if pattern.search(text):
                    problems.append(f'{rel}: {label}')
            for match in IPV4.findall(text):
                try:
                    if ipaddress.ip_address(match) in ipaddress.ip_network('100.64.0.0/10'):
                        problems.append(f'{rel}: tailnet IP')
                except ValueError:
                    pass
            for match in EMAIL.findall(text):
                if not EMAIL_OK.search(match):
                    problems.append(f'{rel}: email address')
            lowered = text.lower()
            problems += [f'{rel}: denylisted term' for w in words if w in lowered]
        self.assertEqual(problems, [])


if __name__ == '__main__':
    unittest.main()
