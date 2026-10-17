#!/usr/bin/env python3
"""Import the web installer from a signed commit of the installer repository.

Usage: scripts/import-installer.py INSTALLER_CHECKOUT COMMIT

Replaces static/install/web/ with the commit's web/ (without nginx/, test/ and
serve.py), copies its three header files to server/nginx/ and writes
installer.sha256 with the commit and the SHA-256 of every file.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = 'static/install/web'
HEADERS = {'web/nginx/base.conf': 'server/nginx/website-installer-base.conf',
           'web/nginx/installer.conf': 'server/nginx/website-installer-page.conf',
           'web/nginx/general.conf': 'server/nginx/website-installer-general.conf'}


def git(checkout, *args):
    return subprocess.run(['git', '-C', checkout, *args], check=True, capture_output=True).stdout


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    checkout, ref = sys.argv[1:]
    commit = git(checkout, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()
    git(checkout, 'verify-commit', commit)
    files = {}
    for name in git(checkout, 'ls-tree', '-r', '-z', '--name-only', commit, 'web').decode().split('\0'):
        if not name:
            continue
        rel = name[len('web/'):]
        if name in HEADERS:
            target = HEADERS[name]
        elif rel.startswith(('nginx/', 'test/')) or rel == 'serve.py':
            continue
        else:
            target = STATIC + '/' + rel
        files[target] = git(checkout, 'show', commit + ':' + name)
    if set(HEADERS.values()) - set(files):
        raise SystemExit('the commit lacks a header file')
    shutil.rmtree(ROOT / STATIC, ignore_errors=True)
    for target, data in sorted(files.items()):
        path = ROOT / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    lines = [f'# DiamaneOS/installer {commit}']
    lines += [f'{hashlib.sha256(data).hexdigest()}  {target}' for target, data in sorted(files.items())]
    (ROOT / 'installer.sha256').write_text('\n'.join(lines) + '\n')
    print(f'installer {commit}: {len(files)} files')


if __name__ == '__main__':
    main()
