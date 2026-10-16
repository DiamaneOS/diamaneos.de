#!/bin/sh
# Build the site and check what it produces:
#   - no JavaScript outside install/web/: no <script>, no .js files, no
#     javascript: URLs. No inline event handlers anywhere.
#   - install/web/ holds exactly the web installer files of installer.sha256,
#     and the links between the installer and the site resolve
#   - nothing the Content-Security-Policy would block: no inline style
#     attributes or <style> elements in HTML
#   - no embedded third-party content: no iframe, object, embed or media
#   - only the bounded contact form, posting to the same site
#   - no request to another host: every src, srcset, <link href>, CSS url()
#     and @import stays on this site
#   - fonts served only as WOFF2 (the Latin subset in docs/fonts.md)
#   - the releases feed: Atom with stable entry ids and absolute links, linked
#     from the releases page
# Links (<a href>) to other sites are allowed and listed, because following a
# link is the reader's choice, not a request the page makes.
#
# Usage: scripts/check-output.sh             build into public/, then check
#        scripts/check-output.sh --no-build  check the existing public/
#        OUT=dir scripts/check-output.sh     use another output directory (a
#                                            running `hugo server` rewrites public/)
set -eu

cd "$(dirname "$0")/.."
OUT="${OUT:-public}"
OWN_HOST="${OWN_HOST:-diamaneos.de}"
case "$OWN_HOST" in
  diamaneos.de|staging.diamaneos.de) ;;
  *) echo "Unsupported output hostname." >&2; exit 2 ;;
esac

if [ "${1:-}" != "--no-build" ]; then
  hugo --quiet --cleanDestinationDir --destination "$OUT"
fi
[ -d "$OUT" ] || { echo "No $OUT/ directory; build first." >&2; exit 2; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM

fail=0
bad() { echo "FAIL  $1"; fail=1; }
ok() { echo "ok    $1"; }
if ! python3 scripts/check-security-publication.py "$OUT"; then
  bad "security publication artifacts failed validation"
fi
# The standard's placeholder declares no authorized advertising sellers.
for name in ads.txt app-ads.txt; do
  if printf '%s\n' 'placeholder.example.com, placeholder, DIRECT, placeholder' | cmp -s - "$OUT/$name"; then
    ok "$name declares no authorized advertising sellers"
  else
    bad "$name differs from the advertising opt-out record"
  fi
done
# The setup wizard's short link (/UBL in server/nginx/website.conf) needs its FAQ entry.
if grep -q 'return 301 /faq/#bootloader-locking-setup;' server/nginx/website.conf \
    && grep -q 'id="bootloader-locking-setup"' "$OUT/faq/index.html"; then
  ok "/UBL redirects to an existing FAQ entry"
else
  bad "/UBL does not lead to the bootloader locking FAQ entry"
fi
# Print matches (file:line: text), cut to 160 characters, at most 20 lines.
show() { cut -c1-160 | head -n 20 | sed 's/^/        /'; }

echo "Checking $OUT/ ($(find "$OUT" -type f | wc -l | tr -d ' ') files)"

# 1. JavaScript, allowed only for the web installer
if ! python3 scripts/check-installer.py "$OUT"; then bad "the web installer differs from installer.sha256 or its links"; fi
if grep -rIniE '<script' "$OUT" | grep -v "^$OUT/install/web/" >"$tmp/m"; then
  bad "<script> found outside install/web/:"; show <"$tmp/m"
else ok "no <script> elements outside install/web/"; fi
if find "$OUT" -path "$OUT/install/web" -prune -o -type f \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \) -print | grep . >"$tmp/m"; then
  bad "JavaScript files found outside install/web/:"; show <"$tmp/m"
else ok "no JavaScript files outside install/web/"; fi
if grep -rIniE 'javascript:' "$OUT" | grep -v "^$OUT/install/web/" >"$tmp/m"; then
  bad "javascript: URL found outside install/web/:"; show <"$tmp/m"
else ok "no javascript: URLs outside install/web/"; fi
if grep -rIniE --include='*.html' --include='*.svg' '<[^>]*[[:space:]]on[a-z]+[[:space:]]*=' "$OUT" >"$tmp/m"; then
  bad "inline event handler found:"; show <"$tmp/m"
else ok "no inline event handlers"; fi

# 2. Inline styles in HTML (the page CSP allows style-src 'self' only)
if grep -rIniE --include='*.html' '<style[[:space:]>]|[[:space:]]style[[:space:]]*=' "$OUT" >"$tmp/m"; then
  bad "inline style in HTML:"; show <"$tmp/m"
else ok "no inline styles in HTML"; fi
if grep -rIlE '<style[[:space:]>]' "$OUT" --include='*.svg' >"$tmp/m"; then
  echo "info  SVG files with an internal <style> (served with the SVG policy in docs/SECURITY-HEADERS.md):"
  sed 's/^/        /' "$tmp/m"
fi

# 3. Embedded content, form contract and base URLs
if grep -rIniE --include='*.html' '<(iframe|frame|frameset|object|embed|applet|video|audio|source|track|portal|base)[[:space:]/>]' "$OUT" >"$tmp/m"; then
  bad "embedded content or <base> found:"; show <"$tmp/m"
else ok "no embedded content or <base>"; fi
if ! python3 scripts/check-forms.py "$OUT"; then bad "contact form differs from its bounded contract"; fi

# 4. Requests to other hosts
external() { grep -E '^(https?:)?//' | grep -vE "^(https?:)?//${OWN_HOST}(/|$|:)" || true; }
{
  grep -rhoiE --include='*.html' --include='*.svg' '[[:space:]](src|srcset|poster|data|action|formaction|background|xlink:href)[[:space:]]*=[[:space:]]*"[^"]*"' "$OUT" |
    sed -E 's/^[^=]*=[[:space:]]*"//; s/"$//' | tr ',' '\n' | sed -E 's/^[[:space:]]+//; s/[[:space:]].*$//'
  grep -rhoiE --include='*.html' '<link[^>]*>' "$OUT" | grep -oiE 'href="[^"]*"' | sed -E 's/^href="//; s/"$//'
  grep -rhoiE --include='*.svg' '<(image|use|feImage)[^>]*href="[^"]*"' "$OUT" | grep -oiE 'href="[^"]*"' | sed -E 's/^href="//; s/"$//'
  grep -rhoiE --include='*.css' 'url\([^)]*\)' "$OUT" | sed -E "s/^url\([[:space:]]*['\"]?//; s/['\"]?[[:space:]]*\)$//"
  grep -rhoiE --include='*.css' '@import[^;]*' "$OUT" | grep -oE "(https?:)?//[^'\")[:space:]]+"
} >"$tmp/res" || true
external <"$tmp/res" | sort -u >"$tmp/m"
if [ -s "$tmp/m" ]; then bad "resources loaded from other hosts:"; show <"$tmp/m"; else ok "no resources from other hosts ($(sort -u "$tmp/res" | wc -l | tr -d ' ') distinct resource URLs, all on this site)"; fi

# 5. Fonts: WOFF2 only
if find "$OUT" -type f \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.woff' -o -iname '*.eot' \) | grep . >"$tmp/m"; then
  bad "font files other than WOFF2:"; show <"$tmp/m"
else ok "fonts are WOFF2 only ($(find "$OUT" -type f -iname '*.woff2' | wc -l | tr -d ' ') files)"; fi

# 6. Every URL to another host in HTML must be a link the reader follows
grep -rhoE --include='*.html' 'https?://[^"'"'"' <>)]+' "$OUT" | external | sort -u >"$tmp/all"
grep -rhoiE --include='*.html' '<a[[:space:]][^>]*href="https?://[^"]*"' "$OUT" | grep -oE 'https?://[^"]+' | external | sort -u >"$tmp/links"
comm -23 "$tmp/all" "$tmp/links" >"$tmp/m"
if [ -s "$tmp/m" ]; then bad "URLs to other hosts outside <a href> in HTML:"; show <"$tmp/m"; else ok "every URL to another host in HTML is a plain link"; fi

# 7. The releases feed and its autodiscovery link
if ! python3 scripts/check-feed.py "$OUT" "$OWN_HOST"; then bad "releases feed failed its checks"; fi
if grep -q 'location = /releases.atom {' server/nginx/website.conf; then
  ok "the feed has its nginx location with the Atom type"
else bad "server/nginx/website.conf has no location for the feed"; fi
if grep -q '<link rel="alternate" type="application/atom+xml"[^>]*href="/releases.atom"' "$OUT/releases/index.html"; then
  ok "the releases page links its feed"
else bad "the releases page does not link its feed"; fi

echo
echo "Links to other sites (navigation only, not loaded by the page):"
if [ -s "$tmp/links" ]; then sed 's/^/        /' "$tmp/links"; else echo "        none"; fi

echo "URLs to other hosts in other text files (not requests: licence text, XML namespaces):"
grep -rIoE --exclude='*.html' --exclude='*.css' 'https?://[^"'"'"' <>)]+' "$OUT" | grep -v "^$OUT/install/web/" |
  grep -vE ":https?://${OWN_HOST}(/|$)" | sort -u | sed 's/^/        /' || true
echo "The web installer under install/web/ may connect only to: $(sed -n 's/.*connect-src \([^;]*\);.*/\1/p' server/nginx/website-installer-page.conf)"

echo
if grep -q 'name="robots" content="noindex' "$OUT/index.html"; then
  echo "info  draft notice is on: pages carry noindex and the draft banner (params.draftNotice in hugo.toml)"
else
  echo "info  draft notice is off: pages can be indexed"
fi

echo
if [ "$fail" -eq 0 ]; then echo "All checks passed."; else echo "Some checks failed."; fi
exit "$fail"
