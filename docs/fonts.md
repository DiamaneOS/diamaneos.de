# Fonts

The site uses one font file: `static/fonts/SofiaSans-latin-wght.woff2`, a Latin subset of Sofia Sans, converted to
WOFF2. It keeps the full weight axis (1 to 1000), the OpenType layout features for the kept characters and every name
table entry, including the copyright and licence entries.

## Source

| | |
| --- | --- |
| Font | Sofia Sans, variable weight (`SofiaSans[wght].ttf`), version 4.101 |
| Upstream | <https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/sofiasans> |
| Source file SHA-256 | `a3e1019b8867e21b75d26a7b59d4eb2c81d1acf6b69b9ae6cedca269fb68e291` (345 684 bytes) |
| Copy used | the DiamaneOS brand files' `SofiaSans[wght].ttf`, same hash |
| Result | `static/fonts/SofiaSans-latin-wght.woff2`, 59 212 bytes |
| Result SHA-256 | `dcd0aedaa4f7b473c73bd90af3a6d126f73d9b7b4bed89dc266d549d834bc1c6` |
| Tools | fontTools 4.66.1 and brotli 1.2.0 (pip), Python 3.14.6, in a throwaway virtual environment |

## Command

Generated once on 30 September 2026. Only the result is committed.

```sh
python3 -m venv fontenv
fontenv/bin/pip install fonttools==4.66.1 brotli==1.2.0

fontenv/bin/pyftsubset "SofiaSans[wght].ttf" \
  --unicodes="U+0000-017F,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD" \
  --layout-features='*' --name-IDs='*' --name-legacy --name-languages='*' \
  --flavor=woff2 --output-file=SofiaSans-latin-wght.woff2

shasum -a 256 SofiaSans-latin-wght.woff2
```

The character set is Basic Latin, Latin-1 Supplement and Latin Extended-A (so names and addresses from most European
languages render in Sofia Sans), plus general punctuation, the euro sign, the trademark sign and a few symbols. The
`unicode-range` in `assets/css/site.css` lists the same ranges. Keep the two in step. Characters outside the subset
fall back to the system font.

To add characters, rerun the command with a wider `--unicodes` list, update the hashes and size here, and update the
`unicode-range`.

## Licence

Sofia Sans is licensed under the SIL Open Font License 1.1 (`static/fonts/OFL.txt`, published at `/fonts/OFL.txt`).
The subset is a Modified Version under that licence and is distributed under the same licence. The font has no
Reserved Font Name, so the modified version may keep the name Sofia Sans. Copyright: 2019 The Sofia Sans Project
Authors (<https://github.com/lettersoup/Sofia-Sans>).
