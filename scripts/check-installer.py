#!/usr/bin/env python3
"""Check the web installer in the source and in a built site.

Usage: scripts/check-installer.py OUT

- Every file in installer.sha256 has its SHA-256, in the source and, for
  static/install/web/, in OUT/install/web/. Neither folder has other files.
- Links from the installer pages to the site, and from the site to the
  installer pages, lead to a file that exists and to an id on that page.
"""
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
STATIC = 'static/install/web/'


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])


def files(folder):
    return {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()} if folder.is_dir() else set()


def main():
    out = Path(sys.argv[1])
    failures = []
    lines = (ROOT / 'installer.sha256').read_text().splitlines()
    if not re.fullmatch(r'# DiamaneOS/installer [0-9a-f]{40}', lines[0]):
        raise SystemExit('installer.sha256 does not name an installer commit')
    listed = dict(reversed(line.split('  ', 1)) for line in lines[1:])
    for name, digest in sorted(listed.items()):
        copies = [ROOT / name] + ([out / 'install/web' / name[len(STATIC):]] if name.startswith(STATIC) else [])
        for path in copies:
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append(f'differs from installer.sha256: {path}')
    expected = {name[len(STATIC):] for name in listed if name.startswith(STATIC)}
    for folder in (ROOT / STATIC, out / 'install/web'):
        failures += [f'not in installer.sha256: {folder / name}' for name in sorted(files(folder) - expected)]

    pages = {}

    def page(path):
        if path not in pages:
            pages[path] = Page(path.read_text()) if path.is_file() else None
        return pages[path]

    def check(source, href):
        url = urlsplit(href)
        if url.scheme or url.netloc or not (url.path or url.fragment):
            return
        target = (source.parent / url.path) if url.path and not url.path.startswith('/') else out / url.path.lstrip('/')
        if not url.path:
            target = source
        if url.path.endswith('/') or target.is_dir():
            target = target / 'index.html'
        found = page(target.resolve())
        if found is None:
            failures.append(f'{source.relative_to(out)}: link to missing {href}')
        elif url.fragment and url.fragment not in found.ids:
            failures.append(f'{source.relative_to(out)}: no id for {href}')

    for path in sorted(out.rglob('*.html')):
        installer = (out / 'install/web') in path.parents
        for href in page(path.resolve()).links:
            if installer or urlsplit(href).path.startswith('/install/web/'):
                check(path, href)
    for failure in failures:
        print('FAIL  ' + failure)
    if failures:
        raise SystemExit(1)
    print(f'ok    web installer {lines[0].split()[-1][:12]}: {len(listed)} files as in installer.sha256, links resolve')


if __name__ == '__main__':
    main()
