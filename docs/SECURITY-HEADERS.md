# Hosting and security headers

The site is plain static files: HTML, one stylesheet, one font, one SVG icon, a licence text, `robots.txt`, a
sitemap, the releases feed and the allowed signers file. It has no JavaScript, no cookies or embedded requests to other hosts. Its contact form posts to the same site (`scripts/check-output.sh` checks
the build).

Serve `public/` through nginx with the same-origin contact handler. The nginx example uses no request logs.
Use the supplied contact proxy configuration. It drops unrelated incoming headers and limits request size and rate.

- **Certificates:** use the host's ACME client and certificate-access controls.
- **Logs:** disable access logs and discard request-associated error logs. Operational journals use volatile storage with a one-day limit.
- **Redirects:** redirect alternative website names to `https://diamaneos.de` after their DNS and certificates are configured.

`hugo.toml` (`[server.headers]`) sends the same security headers during `hugo server`, except HSTS, so the local
preview runs under the same policy. Keep the two in step.

## Headers on every response

```text
Content-Security-Policy: default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), hid=(), magnetometer=(), microphone=(), payment=(), serial=(), usb=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
X-Frame-Options: DENY
```

| Header | Why |
| --- | --- |
| `Content-Security-Policy` | Nothing loads unless listed. Styles, images and fonts come only from this site. No scripts, no connections, no frames, no objects or media. Forms can submit only to the same origin. `style-src 'self'` also blocks inline `style` attributes and `<style>` elements, so templates must not emit them. `frame-ancestors 'none'` stops other sites framing the pages. |
| `X-Content-Type-Options` | Browsers use the declared type and do not guess. |
| `Referrer-Policy` | No referrer is sent to other origins. Same-origin form requests retain their Origin header in browsers that apply this policy to it. External links also carry `rel="noreferrer"`. |
| `Permissions-Policy` | Turns off device APIs the site never uses. |
| `Cross-Origin-*` | Keeps the pages in their own browsing context group and stops other sites embedding the files. |
| `X-Frame-Options` | Older browsers' version of `frame-ancestors 'none'`. |

Each page also carries the same CSP in a `<meta http-equiv>` tag (without `frame-ancestors`, which a meta tag cannot
set) and `<meta name="referrer" content="same-origin">`, as a fallback if a header is missing. The header is the real
control.

## HSTS, without preload

The website sends host-scoped HSTS over HTTPS:

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

- `includeSubDomains`: every diamaneos.de name serves HTTPS. The plain-HTTP connectivity checks run on diamane.de, which never sends HSTS.
- **No `preload`.** Preloading builds the rule into browsers for the domain and all its subdomains. Removal
  takes months to reach users, so a mistake is hard to undo.
- Send HSTS only over HTTPS. nginx redirects website HTTP requests to the canonical HTTPS name.

## SVG files

`favicon.svg` (the brand icon, unmodified) switches between its light and dark drawings with an internal `<style>`.
The page policy (`style-src 'self'`) would block that inside the SVG document, so SVG responses get their own, stricter
policy:

```text
Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox
```

An SVG loaded as an image cannot run scripts anyway. `sandbox` and `default-src 'none'` cover it when opened directly.

## Well-known files

- **PGP key (Web Key Directory):** `/.well-known/openpgpkey/` needs its own content type and CORS headers, see
  `docs/wkd.md`.
- **security.txt:** `/.well-known/security.txt`, see `docs/security-txt.md`.

## Releases feed

`/releases.atom` is served as `application/atom+xml; charset=utf-8` with `Cross-Origin-Resource-Policy: cross-origin`. Thunderbird fetches feeds from another origin ([bug 1698755](https://bugzilla.mozilla.org/show_bug.cgi?id=1698755)), as GrapheneOS notes for its own feed. Its location in `server/nginx/website.conf` repeats the other headers.

## Not sent

- No `Set-Cookie`. The site has no sessions.
- No `Access-Control-Allow-Origin`, except on the WKD path.
- No `Server` header where the server allows removing it.

## nginx

Pair nginx with the host's ACME client. Put the zone from `server/contact/nginx.example.conf` in `http{}` and its location in the website server block. The backend listener is `/run/diamaneos-contact/ingress.sock`. The proxy sends only its five required headers.

`server/nginx/website.conf` supplies the production website virtual hosts. It
uses `website-headers.conf`, a dedicated certificate and a read-only static
directory. Include it in the existing hardened HTTP context after provisioning
its certificate, content and contact services.

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name diamaneos.de;
    root /path/to/public;

    server_tokens off;
    access_log off;
    error_log /dev/null crit;
    error_page 404 /404.html;

    # Define the contact rate-limit zone in http{} and use the location from:
    # server/contact/nginx.example.conf

    add_header Content-Security-Policy "default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "same-origin" always;
    add_header Permissions-Policy "accelerometer=(), camera=(), geolocation=(), gyroscope=(), hid=(), magnetometer=(), microphone=(), payment=(), serial=(), usb=()" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Resource-Policy "same-origin" always;
    add_header Cross-Origin-Embedder-Policy "require-corp" always;
    add_header X-Frame-Options "DENY" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # nginx replaces, not merges, add_header sets inside a location: repeat the
    # headers that still apply.
    location ~* \.svg$ {
        add_header Content-Security-Policy "default-src 'none'; style-src 'unsafe-inline'; sandbox" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Cross-Origin-Resource-Policy "same-origin" always;
    }
}
```

Certificates and the HTTP-to-HTTPS and domain redirects are left out of the nginx example.

## Checking a deployment

```sh
curl -sI https://diamaneos.de/ | grep -iE 'content-security|strict-transport|referrer|permissions|cross-origin|x-content|x-frame|server'
curl -sI https://diamaneos.de/favicon.svg | grep -i content-security
curl -sI https://diamaneos.de/releases.atom | grep -iE 'content-type|cross-origin-resource'
curl -sI https://www.diamaneos.de/ | grep -i location
```

Then open the site with the browser's developer tools and confirm the console shows no policy violations and the
network panel shows requests to `diamaneos.de` only.
