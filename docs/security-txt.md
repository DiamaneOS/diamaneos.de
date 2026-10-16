# security.txt

The clear-signed reporting file is `static/.well-known/security.txt`. Its canonical URL is <https://diamaneos.de/.well-known/security.txt>. The `Encryption` field points to the armoured certificate at `/security-public.asc`.

## Integrity

Preserve the signed file byte-for-byte. A field change or renewal requires a replacement clear-signed artifact. Do not rewrite its line endings, signature or expiry during the website build.

`scripts/check-security-publication.py` verifies the signature against `static/security-public.pgp`, checks the reporting address and certificate URL, and rejects an expired file. It also compares the built copy with the source.

The primary and subkey fingerprints are in `static/security-fingerprints.txt`. The Security page and organization security policy publish the primary fingerprint for comparison.

## Serving

The exact route in `server/nginx/website.conf` serves the file as `text/plain; charset=utf-8`, accepts GET and HEAD, and inherits the website security headers. It takes precedence over the general dotfile refusal.

Build the complete output with `OUT=public scripts/check-output.sh`. Deploy the checked static files together with the nginx routes so the reporting file and its encryption URL are available together.

## Checks

Check the response headers after deployment. Download the signed file and certificate, compare their bytes with the checked output, and verify the signature again. The reporting file's own `Expires` field is the source of truth for renewal.

```sh
curl --fail --silent --show-error --head https://diamaneos.de/.well-known/security.txt
report_check_home=$(mktemp -d)
gpgv --homedir "$report_check_home" --keyring "$PWD/static/security-public.pgp" static/.well-known/security.txt
rmdir "$report_check_home"
```

Reference: [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116.html).
