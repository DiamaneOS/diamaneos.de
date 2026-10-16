# DiamaneOS website

The source of [diamaneos.de](https://diamaneos.de/), built with [Hugo](https://gohugo.io/).

The site is plain HTML and CSS. It has no JavaScript, cookies, analytics or third-party content. The font, the icon and the stylesheet are served from the site itself. The contact form posts to the site's own handler.

## Security reports

Send confidential vulnerability reports to [security@diamaneos.de](mailto:security@diamaneos.de), encrypted with the [OpenPGP public key](https://diamaneos.de/security-public.asc). Follow the [security reporting instructions](https://diamaneos.de/security/) to check its fingerprint. Use the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues) for other bugs.

## Requirements

Hugo 0.146 or later. It is tested with Hugo 0.167.0 (extended). On macOS: `brew install hugo`. The site uses no Node.js, theme or Hugo modules.

Build checks also need Python 3 and GnuPG (`gpg`, `gpgv`).

## Preview

```sh
hugo server --disableLiveReload
```

Then open <http://localhost:1313/> and reload by hand after an edit. The preview sends the same security headers as the host (`[server.headers]` in `hugo.toml`), and that policy blocks Hugo's live-reload script. The contact form needs the separate handler in `server/contact/`.

## Build and check

```sh
OUT=/path/to/output scripts/check-output.sh
```

This builds the site into `OUT` (default `public/`) and checks the output. It fails on any script, inline style, embedded content, resource from another host, font other than WOFF2, or contact form that differs from its bounded contract. It lists every link to another site. `--no-build` checks an existing output directory.

For the staging host, build with `hugo --cleanDestinationDir --baseURL https://staging.diamaneos.de/ --destination DIR` and check with `OWN_HOST=staging.diamaneos.de OUT=DIR scripts/check-output.sh --no-build`.

While `draftNotice = true` in `hugo.toml`, every page shows a draft banner and carries `noindex`. It is `false` for the live site.

## Deployment

The checked output is the whole site. The host serves it with:

- `server/nginx/website.conf` and `website-headers.conf`: the site, the redirects from other names and the contact proxy, inside an existing hardened nginx setup.
- `docs/SECURITY-HEADERS.md`: the Content-Security-Policy and other headers, HSTS, and how to check them on the host.
- `server/contact/README.md`: the contact handler and its deployment contract. Generated files contain no mail credentials.

[`docs/security-txt.md`](docs/security-txt.md) describes the signed reporting file. [`docs/wkd.md`](docs/wkd.md) describes public key discovery and its nginx routes.

## Where things are

| Path | What |
| --- | --- |
| `content/` | One Markdown file per page. The home page is `_index.md`. |
| `data/features.toml` | The Features list. Only features that exist and passed testing on a phone. |
| `data/devices.toml` | The supported devices with their codenames and facts. The only place that names a device. |
| `layouts/` | Templates, partials, shortcodes and render hooks for links and tables. |
| `assets/css/site.css` | The only stylesheet, minified and fingerprinted at build time. |
| `assets/brand/` | Brand SVGs, inlined at build time. Provenance in `assets/brand/SOURCE.md`. |
| `static/` | Copied as is: the favicon, the font subset and its licence, `ads.txt` and `app-ads.txt`. |
| `docs/` | Security headers, the font subset (`fonts.md`), `security.txt` and Web Key Directory notes. |

## Writing pages

- Markdown cannot contain raw HTML (`unsafe = false`). Use the shortcodes.
- Write links inside the site as `/page/`. The build stops if one points to a page that does not exist.
- Links to other sites get `rel="noreferrer"`.

## Design

The site follows the DiamaneOS interface design: Sofia Sans, the colour roles of the Sodium seed `#FBA700` in light and dark, radii of 4, 8 and 12 px, and one plain column. Lamps show colour only where something is on, so nothing on the site is lit. Text contrast is at least 5.8:1 in both themes. Pages have landmarks, a skip link, one `h1` and a visible focus ring, and nothing needs a script.

## Licence

Apache-2.0 for the site's code and text (`LICENSE`, `NOTICE`). The font and the brand files keep their own terms.
