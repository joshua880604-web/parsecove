# ParseCove

A browser-local developer toolbox with seven statically generated pages. The production domain is `https://parsecove.com`.

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

## Publication and SEO

The canonical origin is `https://parsecove.com`, defined in `build.py`. DNS validation and HTTPS issuance must finish before the custom domain serves traffic. The site includes indexable static descriptions, examples, source references and a sitemap. Submit the production-domain sitemap to Search Console after launch. The existing `.openai/hosting.json` records the previous Sites deployment; Cloudflare Pages uses the build settings above and the contents of `dist`. No traffic, ranking, or earnings claims are made.

## Limits

- Timestamps: integer seconds/milliseconds; timezone-explicit ISO inputs with up to millisecond precision; JavaScript Date range; batch maximum 2,000 rows.
- PX/REM: numeric input only, up to 1,000 values, explicit positive root size, 0–8 decimal places.
- Base64 text: UTF-8, standard/Base64URL, strict invalid-input handling.
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

The four tool pages keep their stable URLs and include statically rendered task-specific reference sections. PX/REM common values are rendered at a 16px root for no-JavaScript readers, then updated using the selected root and precision. Numeric example buttons always select PX-to-REM mode explicitly.

The timestamp page includes a device-clock display refreshed once per second. Pause freezes both units; copying also pauses so copied values stay visible. The display is not a synchronized time service. JavaScript and Python examples use explicit UTC instants.

`dist/assets/examples/` contains original 320×180 PNG, JPEG and WebP fixtures. `image-examples.js` contains the same bytes as Base64 for in-browser examples. Downloads preserve these bytes; no format conversion or compression is performed. Image errors link to an on-page troubleshooting reference.

`python3 tests/content_updates.py` checks live-clock pause/copy, original image download bytes, MIME mismatch handling, PX examples/root changes, metadata and five responsive widths against localhost:3000.
