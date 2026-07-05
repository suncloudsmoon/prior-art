# UI Harvest Playbook

How to capture reference UI into `.ref/` so it's actually useful later.

## Contents
- [Brand starter map](#brand-starter-map)
- [What to capture per brand](#what-to-capture-per-brand)
- [Using harvest.py](#using-harvestpy)
- [When Bash has no network: WebFetch fallback](#webfetch-fallback)
- [Screenshots](#screenshots)
- [JS-heavy sites](#js-heavy-sites)
- [Curating tokens.md](#curating-tokensmd)
- [INVENTORY.md template](#inventorymd-template)

## Brand starter map

When the user doesn't name brands, pick 2–4 that match the product's domain. This list is a starting point, not a ceiling — prefer whatever is genuinely excellent and closest to the task.

| Building | Strong references |
|---|---|
| Dev tools, SaaS dashboards | Linear, Vercel, Raycast, PostHog |
| Fintech, payments, billing | Stripe, Mercury, Ramp |
| Marketing sites, landing pages | Stripe, Linear, Framer, Figma |
| Consumer apps | Airbnb, Notion, Spotify, Apple |
| Documentation | Stripe Docs, Tailwind Docs, Vite Docs |
| E-commerce | Apple Store, Shopify storefronts (e.g. Allbirds) |
| Data / analytics UI | Amplitude, PostHog, Grafana |
| Design & creative tools | Figma, Framer, Rive |
| AI products | Claude.ai, Perplexity, Runway |

Pick for *relevance to the task*, not fame: harvesting Stripe's homepage doesn't help a settings-page redesign — harvest a great settings page instead.

## What to capture per brand

Capture the pages that answer the task. Common sets:

- Landing/marketing task → homepage, one product page, pricing page
- App UI task → app screenshots (marketing pages often show app shots in high res), docs UI, changelog
- Component-level task (tables, forms, nav) → the specific pages that showcase that component

Directory shape:

```
.ref/
├── INVENTORY.md
├── linear-app/
│   ├── MANIFEST.md        # what harvest.py saved, what failed
│   ├── page.html
│   ├── css/
│   ├── assets/            # fonts, images
│   ├── shots/             # screenshots, if browser available
│   ├── tokens-raw.md      # auto-extracted (script)
│   └── tokens.md          # curated (you)
└── stripe-com-pricing/
    └── ...
```

## Using harvest.py

```bash
python3 <skill-dir>/scripts/harvest.py <url> [--name NAME] [--out .ref] [--max-assets 40]
```

- One invocation per page. `--name` defaults to a slug of the domain + path (`stripe-com-pricing`).
- It downloads the HTML, all linked + `@import`ed stylesheets, and the fonts/images those stylesheets and the page reference; rewrites URLs so the copy opens locally; extracts `tokens-raw.md`; writes `MANIFEST.md` including anything that failed.
- It is stdlib-only Python; no installs needed.
- Failures of individual assets are normal (CDN auth, 403s) — check MANIFEST.md, only re-try what matters.

## WebFetch fallback

If `harvest.py` can't reach the network (sandboxed Bash, blocked egress), do the same job manually:

1. WebFetch the page URL asking for the raw HTML/structure; save what you get to `.ref/<brand>/page.md` (or `.html` if you got markup).
2. Find stylesheet URLs in the fetched content; WebFetch each and save under `css/`.
3. Extract tokens from that CSS into `tokens-raw.md` by hand (same categories as the script: custom properties, font stacks, colors).
4. Note in MANIFEST.md that this was a WebFetch capture and screenshots/assets are missing.

A partial archive with honest MANIFEST notes beats no archive.

## Screenshots

Rendered captures are the ground truth for how the UI actually looks. In order of preference:

1. A browser tool already in the session (Playwright MCP, agent browser): navigate, full-page screenshot, plus viewport shots of key sections. Save to `shots/`.
2. Playwright CLI (downloads a browser on first run, ~100MB — fine on a dev machine, skip if that's disruptive):
   ```bash
   npx -y playwright@latest screenshot --full-page --viewport-size=1440,900 <url> .ref/<brand>/shots/full.png
   ```
3. No browser available → skip silently; the HTML/CSS/tokens harvest still carries most of the value. Note the gap in MANIFEST.md.

## JS-heavy sites

Sites like Linear or Stripe render much of their UI with JavaScript; raw HTML capture still yields the CSS (where the design tokens live) but the saved page may look skeletal when opened locally. That's expected and fine:

- The **tokens and CSS are the durable value** — they survive even when the page won't render offline.
- If styles seem missing entirely (CSS-in-JS apps), the styles live in JS bundles: grep the downloaded HTML for `<style>` blocks (the script already includes inline styles in token extraction), or take screenshots + read computed styles via a browser tool instead.
- Never conclude "couldn't harvest" just because the local page.html renders poorly — check whether CSS and tokens landed.

## Curating tokens.md

`tokens-raw.md` is a frequency dump; `tokens.md` is a token profile someone can design from. Rules of the document: every value is quoted from the harvested CSS (or a screenshot measurement) with units intact; anything estimated is marked *(inferred)*; tables carry the values, prose carries the judgment. Structure:

```markdown
# <Brand> — token profile

| | |
|---|---|
| Sources | <urls> |
| Captured | <date>, harvest.py (<n> stylesheets) + <method for anything else> |
| Gaps | <e.g. "no rendered screenshots — no browser in session"> |

## Color
| Role | Value | Notes |
|---|---|---|
| Surface / base | `#08090A` | app background |
| Surface / raised | `#101113` | cards, popovers |
| Text / primary | `#F7F8F8` | |
| Text / secondary | `rgba(255,255,255,.7)` | |
| Accent / action | `#5E6AD2` | buttons, links, focus |
| Border | `rgba(255,255,255,.06)` | borders are white-alpha, not gray |

## Typography
- Stack: `"Inter Variable", system-ui, sans-serif`
- Scale: `13 / 14 / 16 / 21 / 40px` — ratio ≈1.25 above 16 *(inferred)*
- Weights: 400 / 510 / 590; body leading `1.5`, headings `1.1`

## Spacing & shape
- Base unit: 4px; observed steps `8, 12, 16, 24, 32, 48`
- Radii: `4px` controls, `8px` cards, `9999px` pills

## Elevation & motion
- Shadows: `0 8px 24px rgba(0,0,0,.35)` (popovers), ...
- Motion: `160ms ease-out` hover, `240ms cubic-bezier(.25,.1,.25,1)` panels

## Signature
2–4 sentences: the moves that create the brand's feel (e.g. "near-black surfaces, a single desaturated accent, tight leading, borders built from white at 6% alpha instead of gray — depth comes from alpha layering, not shadows").
```

The Signature section matters most — it's the judgment a designer can't get from the raw dump.

## INVENTORY.md template

INVENTORY.md is a reference audit, not a file listing — it should read like a senior design engineer prepared it for a teammate who will make decisions from it without re-doing the harvest.

```markdown
# Reference audit — <project>

| | |
|---|---|
| Prepared | <date> |
| Task context | <one line: what this project is, what design work is coming> |
| Method | harvest.py against live production CSS; screenshots <taken / skipped: reason> |
| References | linear.app (homepage), stripe.com/pricing, ... |

## Brand profiles

### Linear — linear.app (homepage)
- Captured: page.html, 68 stylesheets, 5 assets, token profile (`linear-app/tokens.md`)
- Adoption candidates for this project:
  - <2-4 bullets, each tying a concrete pattern to a concrete need of THIS project,
     with a pointer: "alpha-layered borders (tokens.md → Color) for our dense tables">

### <next brand> ...

## Comparison

| | Linear | Stripe | ... |
|---|---|---|---|
| Base spacing unit | 4px | 4px | |
| Type scale | 13–40px, ≈1.25 | 15–48px, ≈1.33 | |
| Palette strategy | near-black + 1 accent | white + gradient accents | |
| Radius philosophy | 4/8px, tight | 8/16px, soft | |
| Depth | alpha borders | layered shadows | |

Where the references agree, that's the settled convention — deviating needs a reason.

## Direction proposal
3–6 bullets: what this project should take from the references and why it fits
this product. This is the input to the design phase (impeccable), not a design.
```

Present the direction proposal and the comparison highlights in chat; point at `.ref/` for the rest. Then suggest running impeccable with `.ref/` as reference material.
