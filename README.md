# prior-art

A Claude Code plugin for the reflex every strong team has: **before building anything, study how the best already solved it — then copy what works.**

It has two modes, plus one always-on convention:

- **UI harvest** — captures reference interfaces from brands with excellent design (Linear, Stripe, whatever fits your domain) into a gitignored `.ref/` archive: live production HTML and CSS, fonts and assets, auto-extracted design tokens, and a curated per-brand token profile. It ends with a reference audit (`INVENTORY.md`): provenance, adoption candidates, a cross-brand comparison matrix, and a direction proposal for *your* project.
- **Research** — for everything else (software architecture, algorithms, hardware, tooling, workflows, best-known methods): finds 3–5 strong existing implementations, documents how each works with tradeoffs and a directly copyable artifact, and presents a single-pick recommendation — **before** anything gets built.
- **Library-first (always on)** — a short convention added to every session and subagent: before hand-writing code for an already-solved problem, use this codebase, the standard library, an installed dependency, then a well-known library, in that order. It doesn't wait for Claude to load a skill, so it doesn't depend on the model choosing to, and every subagent gets its own copy.

It pairs with a design-execution skill (e.g. impeccable): prior-art gathers the evidence, the design skill does the designing. It never designs or implements on its own.

## Install

```bash
claude plugin marketplace add suncloudsmoon/plugins
claude plugin install prior-art@suncloudsmoon
```

Restart Claude Code after installing.

## Usage

Triggers naturally on prompts like:

- "I want this to feel Linear/Stripe quality — set up design references to work from"
- "How do the top API companies do rate limiting? Don't reinvent the wheel."
- "Before I pick parts for this sensor, how do successful products actually do it?"

### What UI harvest produces

```
.ref/                        # gitignored automatically
├── INVENTORY.md             # the audit: provenance, adoption candidates,
│                            # comparison matrix, direction proposal
├── linear-app/
│   ├── MANIFEST.md          # what was captured, what failed, known gaps
│   ├── page.html            # local-viewable copy
│   ├── css/  assets/        # real production stylesheets, fonts, images
│   ├── tokens-raw.md        # auto-extracted custom properties/colors/fonts
│   └── tokens.md            # curated token profile (color roles, type scale,
│                            # spacing, elevation, motion, signature)
└── stripe-com-pricing/ ...
```

`.ref/` is a private, local-only study archive — the designer's swipe file. It is gitignored on creation and never shipped; patterns move into product code only by re-implementation in your project's own idiom.

### What research mode produces

`.ref/prior-art/<topic>.md` — a decision brief: problem and constraints up top, a **single-sentence recommendation first**, then per-exemplar findings (mechanism, why, tradeoffs, copyable artifact, dated and graded sources), a convergence table, and a fit check against your constraints. It proposes; you decide what gets built.

### What library-first does

At session start, and whenever Claude starts a subagent, a hook adds [`hooks/library-first.md`](hooks/library-first.md) (~475 tokens) to Claude's context. It gives Claude a fixed order to check before writing a helper (this codebase, the standard library, an installed dependency, a well-known library), the areas where hand-rolled code most often goes wrong (parsing formats, dates and time zones, validation, crypto, retries, money and more), and one guardrail: no new dependency for what the standard library or one line already does. In the listed areas it prefers a well-known library even over a few handwritten lines, since that's where short hand-rolled code most often hides bugs. When Claude adds a library, it names it in one line. Hard-to-undo choices, such as a framework or a datastore, still go through research mode.

The convention is self-contained, so it works on its own and alongside other plugins that add session context. The hooks only `cat` two pre-built JSON files, so nothing extra needs to be installed. To turn it off, disable the plugin: `claude plugin disable prior-art@suncloudsmoon`.

Measured with `claude plugin eval` (the original 8 cases × 3 runs per arm, regex graders, 2026-10-14): Haiku 5.5 scores 0.85 without the plugin and 1.00 with it; Sonnet 5.5 scores 0.81 without and 1.00 with. The gains come from two cases. Retries with exponential backoff: without the plugin both models hand-roll a sleep loop every time; with it they use a library every time (0.00 → 1.00 on both). Sorting release tags with `semver` already installed, delegated to a subagent: without the plugin Haiku used semver in 2 of 3 runs and Sonnet in none; with it both used it every time. That case measures the main agent and the subagent together, because the main agent sometimes passes the convention along when it delegates. A separate check with only the subagent hook loaded confirmed that subagents receive the convention on their own. A ninth case, added after review, checks that Claude adds a library when nothing suitable is installed: a retry task in a project that uses only the standard library's `urllib.request`. Without the plugin both models hand-rolled a sleep loop in every run; with it, both added a retry library to `requirements.txt` and used it in every run (0.00 → 1.00 on both). In the other five library cases, both models already reach for the standard library or the installed package. The over-correction control (no new dependency for a one-liner) passes with the plugin on both. Cases and fixtures live in `evals/`.

## Bundled tooling

`scripts/harvest.py` — stdlib-only Python (no installs). Fetches a page, downloads its linked and `@import`ed stylesheets plus referenced fonts/images, rewrites URLs so the copy opens locally, extracts a raw token dump, and writes a manifest including anything that failed. Degrades gracefully: JS-heavy sites still yield their CSS and tokens, and the skill falls back to WebFetch when direct network access isn't available.

`hooks/build.py` — stdlib-only Python, for maintainers. Regenerates `hooks/session-start.json` and `hooks/subagent-start.json` from `hooks/library-first.md`. Run it after editing the convention; the tests fail until you do.

## Development

```bash
python3 hooks/build.py                     # after editing hooks/library-first.md
python3 -m unittest discover -s tests -v   # hook wiring
claude plugin validate .                    # manifest, hooks, skill
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
  --model claude-haiku-5-5 --no-publish --max-cost-usd 20   # library-first evals, with vs. without the plugin
```

## License

MIT
