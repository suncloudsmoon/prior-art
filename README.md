# prior-art

A Claude Code plugin for the reflex every strong team has: **before building anything, study how the best already solved it — then copy what works.**

It has two modes, plus one always-on convention:

- **UI harvest** — captures reference interfaces from brands with excellent design (Linear, Stripe, whatever fits your domain) into a gitignored `.ref/` archive: live production HTML and CSS, fonts and assets, auto-extracted design tokens, and a curated per-brand token profile. It ends with a reference audit (`INVENTORY.md`): provenance, adoption candidates, a cross-brand comparison matrix, and a direction proposal for *your* project.
- **Research** — for everything else (software architecture, algorithms, hardware, tooling, workflows, best-known methods): finds 3–5 strong existing implementations, documents how each works with tradeoffs and a directly copyable artifact, and presents a single-pick recommendation — **before** anything gets built.
- **Library-first (always on)** — a short convention added to every session and subagent: before hand-writing code for an already-solved problem, use this codebase, the standard library, an installed dependency, then a well-known library, in that order. It doesn't wait for Claude to load a skill, so it holds on Haiku and Sonnet and inside subagents.

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

At session start, and whenever Claude starts a subagent, a hook adds [`hooks/library-first.md`](hooks/library-first.md) (~475 tokens) to Claude's context. It gives Claude a fixed order to check before writing a helper (this codebase, the standard library, an installed dependency, a well-known library), the areas where hand-rolled code most often goes wrong (parsing formats, dates and time zones, validation, crypto, retries, money and more), and one guardrail: no new dependency for what the standard library or one line already does. When Claude adds a library, it names it in one line. Hard-to-undo choices, such as a framework or a datastore, still go through research mode.

The convention is self-contained, so it works on its own and alongside other plugins that add session context. It needs `python3` on your PATH. To turn it off, disable the plugin: `claude plugin disable prior-art@suncloudsmoon`.

## Bundled tooling

`scripts/harvest.py` — stdlib-only Python (no installs). Fetches a page, downloads its linked and `@import`ed stylesheets plus referenced fonts/images, rewrites URLs so the copy opens locally, extracts a raw token dump, and writes a manifest including anything that failed. Degrades gracefully: JS-heavy sites still yield their CSS and tokens, and the skill falls back to WebFetch when direct network access isn't available.

`hooks/inject.py` — stdlib-only Python. Prints `hooks/library-first.md` as hook context for `SessionStart` and `SubagentStart`.

## Development

```bash
python3 -m unittest discover -s tests -v   # hook wiring
claude plugin validate .                    # manifest, hooks, skill
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
  --model claude-haiku-5-5 --no-publish --max-cost-usd 20   # library-first evals, with vs. without the plugin
```

## License

MIT
