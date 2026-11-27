# ParseCove

A browser-local developer toolbox with twelve statically generated pages. Try it at [parsecove.com](https://parsecove.com/).

## Use the tools

| Tool | What it does |
| --- | --- |
| [Unix timestamp converter](https://parsecove.com/unix-timestamp-converter/) | Convert seconds or milliseconds to dates, convert timezone-explicit dates to timestamps, and check current Unix time. |
| [PX to REM converter](https://parsecove.com/px-to-rem/) | Convert PX to REM or REM to PX with a custom root font size, including lists of values. |
| [REM to PX converter](https://parsecove.com/rem-to-px/) | Start with REM values, set the computed root font size, and copy or download pixel results as CSV. |
| [Base64 decoder and encoder](https://parsecove.com/base64/) | Decode UTF-8 text or encode it using standard Base64 or Base64URL, with explicit padding controls and validation. |
| [Base64URL decoder and encoder](https://parsecove.com/base64url-decode/) | Decode the URL-safe alphabet as UTF-8 text or hex, encode with optional padding, compare standard Base64 and download original bytes. |
| [Base64 to image converter](https://parsecove.com/base64-to-image/) | Preview PNG, JPEG, GIF or WebP bytes and download the original image, or encode a local image as Base64. |
| [Image to Base64 converter](https://parsecove.com/image-to-base64/) | Start with an image file and copy or download a complete data URL, raw Base64, HTML image tag or CSS background declaration. |

The tools are free to use without an account. Conversion inputs are processed in your browser; they are not uploaded to a conversion API. Supported formats, size limits and validation rules are documented on each tool page and below.

## Read the guides

[Developer guides](https://parsecove.com/guides/) connects worked explanations to the conversion tools. The first guide, [REM vs EM](https://parsecove.com/guides/rem-vs-em/), includes a root/parent/child comparison, nested font examples, source references, an in-page glossary and FAQ. The registry, static content and article metadata live in `guide_pages.py`. Guide publication dates are explicit content dates and do not change on every build.

`python3 tests/guides.py` verifies the comparison against actual browser CSS, defaults and invalid inputs, copy, navigation, static content, structured data and responsive layouts.

## Deploy to Cloudflare Pages

Connect `joshua880604-web/parsecove` in **Cloudflare → Workers & Pages → Create application → Pages → Import an existing Git repository**. Use these settings:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Framework preset | `None` |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Root directory | Leave at the repository root |

No dependencies, server, Worker entrypoint, API keys or environment variables are needed for the current build. Git integration deploys future pushes to `main` automatically after the initial setup. This checkout alone does not create a Cloudflare project or authorize access to the account.

See [the deployment guide](DEPLOYMENT.md) for custom-domain setup and launch checks.

## Develop

- `python3 build.py` regenerates HTML, canonical metadata, structured data, sitemap and robots.
- `python3 -m http.server 3000 --directory dist` serves the static site.
- `npm test` verifies conversion functions.
- `python3 tests/browser.py` runs browser flows against localhost:3000 with Chromium installed at `/usr/bin/chromium`.

Conversion logic is in `dist/assets/core.js`. UI behavior is in `dist/assets/app.js`. All inputs stay in browser memory. No external scripts, analytics, fonts, APIs, cookies, or input history are added by the application. Hosting access controls may require sign-in independently of the application.

The two image routes share `image_pages.py` and the same byte-validation and encoding logic. `/base64-to-image/` starts with Base64 input; `/image-to-base64/` starts with a local file. The encoder offers complete local examples, clipboard output and text downloads for data URLs, raw Base64, HTML and CSS. It does not fetch remote image URLs or convert image formats.

`python3 tests/image_encoder.py` verifies file selection, PNG/JPEG/GIF/WebP byte round trips, four output formats and downloads, clipboard copy, invalid-file clearing, drag and drop, mode switching, metadata, internal links and responsive layouts against localhost:3000.

`python3 tests/rem_converter.py` checks default and batch conversion, custom roots, rounding, quick examples, clipboard and CSV output, invalid-input clearing, both modes, static metadata and responsive layouts against localhost:3000.

The Base64URL entry point uses the same strict RFC 4648 byte parser as the existing Base64 tool. It accepts URL-safe input only. Valid binary data remains available as hex, standard Base64 and original byte downloads when it is not UTF-8. It does not parse or verify whole JWTs. Its static reference content is in `base64url_page.py`.

`python3 tests/base64url.py` checks padded and unpadded values, Unicode, binary output and downloads, strict validation, both modes, metadata, static content and responsive layouts against localhost:3000. Browser tests accept an alternate origin through `PARSECOVE_TEST_URL`.

## Publication and SEO

The canonical origin is `https://parsecove.com`, defined in `build.py`. DNS validation and HTTPS issuance must finish before the custom domain serves traffic. The site includes indexable static descriptions, examples, source references and a sitemap. Submit the production-domain sitemap to Search Console after launch. The existing `.openai/hosting.json` records the previous Sites deployment; Cloudflare Pages uses the build settings above and the contents of `dist`. No traffic, ranking, or earnings claims are made.

## Limits

- Timestamps: integer seconds/milliseconds; timezone-explicit ISO inputs with up to millisecond precision; JavaScript Date range; batch maximum 2,000 rows.
- PX/REM: numeric input only, up to 1,000 values, explicit positive root size, 0–8 decimal places.
- Base64 text: UTF-8, standard/Base64URL, strict invalid-input handling. The dedicated Base64URL page accepts at most 2 million encoded input characters or 1 MB (1,000,000 bytes) of text to encode.
- Images: PNG/JPEG/GIF/WebP; maximum 10 MB decoded/file size and 40 megapixels for preview. Original byte downloads; no compression or format conversion; SVG is intentionally unsupported.

## Advertising layout hooks (no advertising integration yet)

`ad-slots.json` controls placement markup at build time. `slots_enabled` is **false** by default, so the published HTML has no ad containers, empty reserved gaps or network ad requests. Per-placement switches:

- `home_after_tools`: one placement after the entire tool directory.
- `tool_primary`: one placement after the entire workbench, outside inputs, results, copy and download controls.
- `tool_secondary`: an optional placement after explanations/FAQ and before related tools; off by default and hidden below 1120px even if configured on.

Setting `slots_enabled` to true **only reserves layout containers**; it does not load ads. There is deliberately no publisher ID, ad-network script, ad request, fabricated ads.txt, or consent stub.

For isolated local layout QA (never deploy this preview):

```sh
PARSECOVE_AD_PREVIEW=1 PARSECOVE_BUILD_DIR=/workspace/work/parsecove-ad-preview python3 build.py
```

The preview adds non-clickable, clearly labelled placeholders and uses the same responsive slot CSS. Planned surface sizes: up to 320×100 on narrow screens, 468×60 at 900px, 728×90 at 1120px and 970×90 at 1440px. These are layout targets, not a promise of inventory, fill, policy approval or earnings. Actual units must fit their containers. Never clip or resize an ad creative to force a fit.

Before enabling real AdSense: obtain the account's publisher and unit IDs; review placements; implement Google's supported loading and regional consent requirements; update privacy disclosures to reflect actual advertising behavior; add the account's real ads.txt line if provided; and verify layout stability with real ads. Keep conversion inputs/files out of ad requests and analytics. Ad approval and public access are separate from these hooks.

## Conversion references and examples

The seven tool pages keep their stable URLs and include statically rendered task-specific reference sections. PX/REM common values are rendered at a 16px root for no-JavaScript readers, then updated using the selected root and precision. Numeric example buttons select the direction matching their displayed units. The two CSS converter pages share `css_pages.py` and the same conversion function; `/rem-to-px/` starts in REM mode with its own worked examples and reference table. Both pages offer CSV downloads that include the input and output units and root size.

The timestamp page includes a device-clock display refreshed once per second. Pause freezes both units; copying also pauses so copied values stay visible. The display is not a synchronized time service. JavaScript and Python examples use explicit UTC instants.

`dist/assets/examples/` contains original 320×180 PNG, JPEG and WebP fixtures. `image-examples.js` contains the same bytes as Base64 for in-browser examples. Downloads preserve these bytes; no format conversion or compression is performed. Image errors link to an on-page troubleshooting reference.

`python3 tests/content_updates.py` checks live-clock pause/copy, original image download bytes, MIME mismatch handling, PX examples/root changes, metadata and five responsive widths against localhost:3000.
