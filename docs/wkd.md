# Web Key Directory

The direct WKD files map `security@diamaneos.de` to its OpenPGP certificate. The [Security page](https://diamaneos.de/security/) provides the reporting instructions and primary fingerprint.

## Files

| Source | Purpose |
| --- | --- |
| `static/security-public.asc` | Armoured OpenPGP certificate. |
| `static/security-public.pgp` | Binary OpenPGP certificate. |
| `static/security-fingerprints.txt` | Primary, signing and encryption fingerprints, in that order. |
| `static/.well-known/openpgpkey/policy` | Empty WKD policy file. |
| `static/.well-known/openpgpkey/hu/t5s8ztdbon8yzntexy6oz5y48etqsnbb` | Binary certificate for the reporting address. |

The WKD filename is the z-base-32 encoded SHA-1 hash of `security`. The binary certificate contains only the reporting address. `scripts/check-security-publication.py` checks the filename, user ID, fingerprints and certificate bytes.

## nginx route

`server/nginx/website.conf` serves the WKD files with a `^~` location, bypassing the general dotfile refusal only for this prefix. Its allowlist exposes the policy and reporting certificate. GET and HEAD are supported. Other methods return 405.

WKD responses use `application/octet-stream`, `Access-Control-Allow-Origin: *` and `Cross-Origin-Resource-Policy: cross-origin`. The location repeats the remaining website headers because nginx replaces inherited `add_header` directives when a location defines its own headers.

The exact `/security-public.asc` and `/security-public.pgp` routes serve `application/pgp-keys`. Other sensitive-file and hidden-path refusals remain in place.

Direct WKD uses the mail domain's HTTPS host. Check A and AAAA records for `openpgpkey.diamaneos.de` before deployment. Clients try the advanced host first and use direct discovery only when it has no address. Wildcard DNS can prevent fallback.

If wildcard DNS supplies that host's address, create an explicit empty TXT record at `openpgpkey.diamaneos.de` and remove any exact A, AAAA or CNAME records there. Address queries must return no address. This keeps other wildcard names intact.

## Checks

Build with `OUT=public scripts/check-output.sh`. The publication check needs GnuPG and `gpgv`. Hugo copies these public files without modification.

After deployment, check both GET and HEAD on the policy and key URLs. Confirm the content types, CORS header and a single cross-origin resource policy. Compare downloaded bytes with the checked output.

```sh
curl --fail --silent --show-error --head https://diamaneos.de/.well-known/openpgpkey/policy
curl --fail --silent --show-error --head 'https://diamaneos.de/.well-known/openpgpkey/hu/t5s8ztdbon8yzntexy6oz5y48etqsnbb?l=security'
```

Use a fresh temporary GnuPG home for discovery so an existing key cannot mask a WKD failure. Require the primary fingerprint from `static/security-fingerprints.txt` and the reporting user ID.

```sh
wkd_check_home=$(mktemp -d)
gpg --homedir "$wkd_check_home" --auto-key-locate clear,nodefault,wkd --locate-keys security@diamaneos.de
gpgconf --homedir "$wkd_check_home" --kill all
rm -r "$wkd_check_home"
```

Reference: [OpenPGP Web Key Directory, key discovery](https://www.ietf.org/archive/id/draft-koch-openpgp-webkey-service-20.html#section-3.1).
