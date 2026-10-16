# DiamaneOS website

The source of [diamaneos.de](https://diamaneos.de/), built with [Hugo](https://gohugo.io/).

The site is plain HTML and CSS. It has no cookies, analytics or third-party content. The font, the icon and the stylesheet are served from the site itself. The contact form posts to the site's own handler.

The only JavaScript is the [web installer](https://github.com/DiamaneOS/installer) at `/install/web/`, as GrapheneOS serves its own. Its files come from a signed installer commit and are checked against `installer.sha256`.

## Security reports

Send confidential vulnerability reports to [security@diamaneos.de](mailto:security@diamaneos.de), encrypted with the [OpenPGP public key](https://diamaneos.de/security-public.asc). Follow the [security reporting instructions](https://diamaneos.de/security/) to check its fingerprint. Use the [issue tracker](https://github.com/DiamaneOS/issue-tracker/issues) for other bugs.

## Requirements

Hugo 0.146 or later. It is tested with Hugo 0.167.0 (extended). On macOS: `brew install hugo`. The site uses no Node.js, theme or Hugo modules.

Build checks also need Python 3 and GnuPG (`gpg`, `gpgv`).

## Preview

```sh
hugo server --disableLiveReload
```

Then open <http://localhost:1313/> and reload by hand after an edit. The contact form needs the separate handler in `server/contact/`.

The preview sends the same security headers as the host (`[server.headers]` in `hugo.toml`), and that policy blocks Hugo's live-reload script and the web installer. Test the installer with its own `web/serve.py`.

## Build and check

```sh
OUT=/path/to/output scripts/check-output.sh
```

This builds the site into `OUT` (default `public/`) and checks the output. It fails on any script outside `install/web/`, inline style, embedded content, resource from another host, font other than WOFF2, or contact form that differs from its bounded contract. `--no-build` checks an existing output directory.

It also fails if a file under `install/web/` differs from `installer.sha256`, or a link between the installer and the site leads nowhere. It lists every link to another site.

For the staging host, build with `hugo --cleanDestinationDir --baseURL https://staging.diamaneos.de/ --destination DIR` and check with `OWN_HOST=staging.diamaneos.de OUT=DIR scripts/check-output.sh --no-build`.

While `draftNotice = true` in `hugo.toml`, every page shows a draft banner and carries `noindex`. It is `false` for the live site.

## Deployment

The checked output is the whole site. The host serves it with:

- `server/nginx/website.conf` and `website-headers.conf`: the site, the redirects from other names and the contact proxy, inside an existing hardened nginx setup.
- `server/nginx/website-installer-*.conf`: the web installer's own headers for `/install/web/`, imported with its files.
- `docs/SECURITY-HEADERS.md`: the Content-Security-Policy and other headers, HSTS, and how to check them on the host.
- `server/contact/README.md`: the contact handler and its deployment contract. Generated files contain no mail credentials.

[`docs/security-txt.md`](docs/security-txt.md) describes the signed reporting file. [`docs/wkd.md`](docs/wkd.md) describes public key discovery and its nginx routes.

## Where things are

| Path | What |
| --- | --- |
| `content/` | One Markdown file per page. The home page is `_index.md`. |
| `data/features.toml` | The Features list. Only features that exist and passed testing on a phone. |
| `data/devices.toml` | The supported devices with their codenames and facts. The only place that names a device. |
| `data/releases/` | One TOML file per release. They make the Releases page and the Atom feed at `/releases.xml`. |
| `layouts/` | Templates, partials, shortcodes and render hooks for links and tables. |
| `assets/css/site.css` | The only stylesheet, minified and fingerprinted at build time. |
| `assets/brand/` | Brand SVGs, inlined at build time. Provenance in `assets/brand/SOURCE.md`. |
| `static/` | Copied as is: the favicon, the font subset and its licence, `ads.txt`, `app-ads.txt` and the commit signing key in `allowed_signers.txt`. |
| `static/install/web/`, `installer.sha256` | The web installer, imported from a signed commit with `scripts/import-installer.py INSTALLER_CHECKOUT COMMIT`. Never edited here. |
| `docs/` | Security headers, the font subset (`fonts.md`), `security.txt` and Web Key Directory notes. |

## Writing pages

- Markdown cannot contain raw HTML (`unsafe = false`). Use the shortcodes.
- Write links inside the site as `/page/`. The build stops if one points to a page that does not exist.
- Links to other sites get `rel="noreferrer"`.

## Adding a release

A release is one new file, `data/releases/VERSION.toml`, named after its version:

```toml
version = "VERSION"
date = YYYY-MM-DD
channels = ["stable", "beta", "alpha"]
notes = '''
- What changed, in Markdown lists and paragraphs.
'''
```

- `channels` lists the update channels that offer the release.
- Two releases on one day need a time, such as `YYYY-MM-DDT18:00:00Z`, so feed readers can order them.
- Each feed entry's id is `https://diamaneos.de/releases/#VERSION`. Never rename or reuse a version.
- The feed carries the newest 20 releases. The build stops on an entry that does not follow this format.

## Design

The site follows the DiamaneOS interface design: Sofia Sans, the colour roles of the Sodium seed `#FBA700` in light and dark, radii of 4, 8 and 12 px, and one plain column. Lamps show colour only where something is on, so nothing on the site is lit. Text contrast is at least 5.8:1 in both themes. Pages have landmarks, a skip link, one `h1` and a visible focus ring, and nothing but the web installer needs a script.

## Licence

Apache-2.0 for the site's code and text (`LICENSE`, `NOTICE`). The font and the brand files keep their own terms.
