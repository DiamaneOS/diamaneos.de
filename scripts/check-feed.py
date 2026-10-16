#!/usr/bin/env python3
"""Check the releases feed in a built site: Atom with stable entry ids and
absolute links to this site. Usage: check-feed.py OUT HOST"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
ID = "https://diamaneos.de/releases/"


def problems(out, host):
    site = f"https://{host}/"
    feed = ET.parse(Path(out) / "releases.atom").getroot()
    if feed.tag != ATOM + "feed":
        return ["not an Atom feed"]
    found = []
    if feed.findtext(ATOM + "id") != ID:
        found.append("feed id changed")
    if not feed.findtext(ATOM + "title") or not feed.findtext(f"{ATOM}author/{ATOM}name"):
        found.append("feed title or author missing")
    if not STAMP.fullmatch(feed.findtext(ATOM + "updated") or ""):
        found.append("feed updated is not an RFC 3339 UTC time")
    links = {link.get("rel"): link.get("href") for link in feed.findall(ATOM + "link")}
    if links.get("self") != site + "releases.atom" or links.get("alternate") != site + "releases/":
        found.append("feed self or alternate link wrong")
    ids = []
    for entry in feed.findall(ATOM + "entry"):
        entry_id = entry.findtext(ATOM + "id") or ""
        version = entry_id.removeprefix(ID + "#")
        ids.append(entry_id)
        link = entry.find(ATOM + "link")
        if not version or entry_id != ID + "#" + version:
            found.append(f"entry id {entry_id!r} is not {ID}#VERSION")
        elif link is None or link.get("href") != f"{site}releases/#{version}":
            found.append(f"{version}: link is not the release on {site}")
        if not all(STAMP.fullmatch(entry.findtext(ATOM + n) or "") for n in ("published", "updated")):
            found.append(f"{version}: dates are not RFC 3339 UTC times")
        if re.search(r'(?:href|src)="(?!https://)', entry.findtext(ATOM + "content") or ""):
            found.append(f"{version}: relative or plain HTTP link in the notes")
    if len(ids) != len(set(ids)) or len(ids) > 20:
        found.append("entry ids repeat or more than 20 entries")
    return found


if __name__ == "__main__":
    found = problems(sys.argv[1], sys.argv[2])
    for problem in found:
        print(f"FAIL  releases feed: {problem}")
    if found:
        sys.exit(1)
    print("ok    releases feed: Atom with stable entry ids and absolute links")
