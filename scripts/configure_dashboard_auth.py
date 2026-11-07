"""Append dashboard credentials on the VPS without reading existing environment values."""
import getpass
import json
import os
from pathlib import Path
import secrets
import sys


def main():
    if len(sys.argv) != 2 or not sys.stdin.isatty():
        sys.exit('Run interactively on the VPS: python3 configure_dashboard_auth.py /project/.env')
    target = Path(sys.argv[1])
    password = getpass.getpass('New dashboard password (at least 24 characters): ')
    if len(password) < 24 or not password.isascii() or '\n' in password or '\r' in password:
        sys.exit('Password must have at least 24 ASCII characters and no newlines.')
    if password != getpass.getpass('Confirm dashboard password: '):
        sys.exit('Passwords did not match; nothing changed.')
    # Dollar signs are rejected because Compose interpolates double-quoted values.
    if '$' in password:
        sys.exit('Use a password without dollar signs to avoid Compose interpolation.')
    values = {
        'HERMES_DASHBOARD_BASIC_AUTH_USERNAME': 'admin',
        'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD': password,
        'HERMES_DASHBOARD_BASIC_AUTH_SECRET': secrets.token_urlsafe(48),
    }
    payload = '\n' + '\n'.join(key + '=' + json.dumps(value) for key, value in values.items()) + '\n'
    flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
    descriptor = os.open(target, flags)
    with os.fdopen(descriptor, 'w') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(payload)
    print('Dashboard login admin configured. No existing environment values were read.')


if __name__ == '__main__':
    main()
