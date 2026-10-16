#!/usr/bin/env python3
"""Check public reporting artifacts without using a personal GnuPG keyring."""

import base64
from datetime import datetime, timezone
from email.utils import parseaddr
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FINGERPRINTS = (
    "4AB91DBA47262048497BA046A6D9A7C648A6884E",
    "7C32C1184D4187765B36965BAE11FCFAB1178029",
    "800642C20B1191225833BECDEBDF417B940EB5A5",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    require(result.returncode == 0, f"{args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def wkd_hash():
    bits = f"{int.from_bytes(hashlib.sha1(b'security').digest(), 'big'):0160b}"
    alphabet = "ybndrfg8ejkmcpqxot1uwisza345h769"
    return "".join(alphabet[int(bits[i:i + 5], 2)] for i in range(0, 160, 5))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.update(value for key, value in attrs if key == "href")


def check(output):
    static = ROOT / "static"
    wkd = f".well-known/openpgpkey/hu/{wkd_hash()}"
    expected = {
        "security-public.asc", "security-public.pgp", "security-fingerprints.txt",
        ".well-known/security.txt", ".well-known/openpgpkey/policy", wkd,
    }
    for directory, allowed in (
        (".well-known", {name for name in expected if name.startswith(".well-known/")}),
    ):
        for base in (static, output):
            actual = {str(p.relative_to(base)) for p in (base / directory).rglob("*") if p.is_file()}
            require(actual == allowed, f"Unexpected or missing public files in {base / directory}")
    for name in sorted(expected):
        source, built = static / name, output / name
        require(source.is_file() and not source.is_symlink(), f"Invalid source: {name}")
        require(built.is_file() and not built.is_symlink(), f"Invalid output: {name}")
        data = source.read_bytes()
        require(data == built.read_bytes(), f"Build changed {name}")
        require(not re.search(rb"-----BEGIN [^-\r\n]*PRIVATE KEY", data), f"Private material: {name}")
    require((static / ".well-known/openpgpkey/policy").read_bytes() == b"", "WKD policy must be empty")
    binary = (static / "security-public.pgp").read_bytes()
    require((static / wkd).read_bytes() == binary, "WKD differs from binary certificate")
    armor = (static / "security-public.asc").read_text()
    encoded = armor.split("\n\n", 1)[1].split("-----END PGP PUBLIC KEY BLOCK-----", 1)[0]
    decoded = base64.b64decode("".join(line for line in encoded.splitlines() if not line.startswith("=")), validate=True)
    require(decoded == binary, "Armoured and binary certificates differ")
    require(tuple((static / "security-fingerprints.txt").read_text().splitlines()) == FINGERPRINTS, "Fingerprint file differs")

    with tempfile.TemporaryDirectory(prefix="diamaneos-public-check-") as home:
        gpg = ["gpg", "--no-options", "--homedir", home, "--batch", "--no-autostart"]
        for name in ("security-public.asc", "security-public.pgp"):
            path = str(static / name)
            records = [line.split(":") for line in run(gpg + ["--with-colons", "--import-options", "show-only", "--import", path]).splitlines()]
            require(tuple(r[9] for r in records if r[0] == "fpr") == FINGERPRINTS, f"Wrong fingerprints: {name}")
            uids = [r[9] for r in records if r[0] == "uid"]
            require(len(uids) == 1 and parseaddr(uids[0])[1] == "security@diamaneos.de", f"Wrong reporting UID: {name}")
            require(all(r[1] not in ("e", "r", "d") for r in records if r[0] in ("pub", "sub")), f"Unusable key: {name}")
            packets = run(gpg + ["--list-packets", path])
            allowed = (":public key packet:", ":public sub key packet:", ":user ID packet:", ":signature packet:")
            require(all(line.startswith(allowed) for line in packets.splitlines() if line.startswith(":")), f"Non-public OpenPGP packet: {name}")
        status = run(["gpgv", "--homedir", home, "--keyring", str(static / "security-public.pgp"), "--status-fd", "1", str(static / ".well-known/security.txt")])
        signatures = [line.split() for line in status.splitlines() if line.startswith("[GNUPG:] VALIDSIG ")]
        require(len(signatures) == 1 and signatures[0][2] == FINGERPRINTS[1] and signatures[0][-1] == FINGERPRINTS[0], "Wrong security.txt signer")

    signed = (static / ".well-known/security.txt").read_text()
    payload = signed.split("\n\n", 1)[1].split("-----BEGIN PGP SIGNATURE-----", 1)[0]
    fields = dict(line.split(": ", 1) for line in payload.splitlines() if line)
    require(fields.get("Contact") == "mailto:security@diamaneos.de", "Wrong security.txt contact")
    require(fields.get("Encryption") == "https://diamaneos.de/security-public.asc", "Wrong encryption URL")
    require(fields.get("Canonical") == "https://diamaneos.de/.well-known/security.txt", "Wrong canonical URL")
    require(fields.get("Preferred-Languages") == "en", "Wrong reporting language")
    expiry = datetime.fromisoformat(fields["Expires"].replace("Z", "+00:00"))
    require(expiry > datetime.now(timezone.utc), "security.txt has expired")
    links = Links()
    links.feed((output / "security/index.html").read_text())
    for name in ("security-public.asc", "security-public.pgp", "security-fingerprints.txt", ".well-known/security.txt"):
        require("/" + name in links.hrefs, f"Missing reporting link: {name}")
    print(f"ok    {len(expected)} public artifacts: exact output copies; OpenPGP identity and signature; WKD; links")
    print(f"ok    security.txt expires {fields['Expires']}; SHA256 {hashlib.sha256((static / '.well-known/security.txt').read_bytes()).hexdigest()}")


if __name__ == "__main__":
    try:
        check(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "public")
    except (ValueError, OSError, KeyError, IndexError) as exc:
        print(f"FAIL  security publication: {exc}", file=sys.stderr)
        sys.exit(1)
