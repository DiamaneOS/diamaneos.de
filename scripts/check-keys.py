#!/usr/bin/env python3
"""Check the public keys in static/keys/ against the values the pages print."""

import base64
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {"avb_pkmd.bin", "avb.pub.pem", "factory.allowed_signers", "apps.0.pub", "release-list.pub.pem"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    require(result.returncode == 0, f"{args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def pem_der(path):
    body = path.read_text().split("-----BEGIN PUBLIC KEY-----\n", 1)[1].split("-----END PUBLIC KEY-----", 1)[0]
    return base64.b64decode("".join(body.split()), validate=True)


def check(output):
    keys, built = ROOT / "static/keys", output / "keys"
    for base in (keys, built):
        require({p.name for p in base.iterdir()} == FILES, f"Unexpected or missing files in {base}")
    for name in FILES:
        data = (keys / name).read_bytes()
        require(data == (built / name).read_bytes(), f"Build changed {name}")
        require(b"PRIVATE" not in data, f"Private material: {name}")
    page = (ROOT / "content/documentation/keys.md").read_text()
    install = (ROOT / "content/install/cli.md").read_text()
    chooser = (ROOT / "content/install.md").read_text()

    # avb_pkmd.bin is the PEM key in AVB's binary form: bit length, n0inv, modulus, r^2 mod n.
    avb = (keys / "avb_pkmd.bin").read_bytes()
    bits, n0inv = struct.unpack(">II", avb[:8])
    size = bits // 8
    require(bits == 4096 and len(avb) == 8 + 2 * size, "avb_pkmd.bin is not an RSA-4096 AVB key")
    modulus = int(run(["openssl", "rsa", "-pubin", "-in", str(keys / "avb.pub.pem"), "-noout", "-modulus"]).split("=")[1], 16)
    require(int.from_bytes(avb[8:8 + size], "big") == modulus, "avb_pkmd.bin and avb.pub.pem differ")
    require((n0inv * modulus) % 2**32 == 2**32 - 1, "avb_pkmd.bin has a wrong n0inv")
    require(int.from_bytes(avb[8 + size:], "big") == pow(2, 2 * bits, modulus), "avb_pkmd.bin has a wrong r^2")
    avb_id = hashlib.sha256(avb).hexdigest()
    require(all(avb_id in text for text in (page, install, chooser)), "A page lacks the verified boot key ID")

    signers = (keys / "factory.allowed_signers").read_text()
    require(re.fullmatch(r"diamaneos ssh-ed25519 [A-Za-z0-9+/=]+\n", signers), "factory.allowed_signers is not one Ed25519 line")
    require(signers.strip() in page, "The page lacks the factory key line")
    fingerprint = run(["ssh-keygen", "-lf", str(keys / "factory.allowed_signers")]).split()[1]
    require(fingerprint in page and fingerprint in install, "A page lacks the factory key fingerprint")

    catalog = (keys / "apps.0.pub").read_text().splitlines()
    require(len(catalog) == 2 and catalog[0] == "untrusted comment: signify public key", "apps.0.pub is not a signify key")
    require(catalog[1] in page, "The page lacks the catalog key")

    key_id = hashlib.sha256(pem_der(keys / "release-list.pub.pem")).hexdigest().upper()
    require(key_id in page, "The page lacks the release list keyId")

    conf = (ROOT / "server/nginx/website.conf").read_text()
    allowed = re.search(r"\^/keys/\(\?:([^)]*)\)\$", conf)
    require(allowed and set(allowed.group(1).replace("\\.", ".").split("|")) == FILES, "nginx /keys/ list differs from static/keys/")
    print(f"ok    {len(FILES)} public keys: exact output copies, AVB forms agree, the pages print their IDs, nginx lists them")


if __name__ == "__main__":
    try:
        check(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "public")
    except (ValueError, OSError, IndexError) as exc:
        print(f"FAIL  public keys: {exc}", file=sys.stderr)
        sys.exit(1)
