# prior-art

A Claude Code plugin for the reflex every strong team has: **before building anything, study how the best already solved it — then copy what works.**

It has two modes, plus one always-on convention:

- **UI harvest** — captures reference interfaces from brands with excellent design (Linear, Stripe, whatever fits your domain) into a gitignored `.ref/` archive: live production HTML and CSS, fonts and assets, auto-extracted design tokens, and a curated per-brand token profile. It ends with a reference audit (`INVENTORY.md`): provenance, adoption candidates, a cross-brand comparison matrix, and a direction proposal for *your* project.
- **Research** — for everything else (software architecture, algorithms, hardware, tooling, workflows, best-known methods): finds 3–5 strong existing implementations, documents how each works with tradeoffs and a directly copyable artifact, and presents a single-pick recommendation — **before** anything gets built.
- **Reuse-first (always on)** — a short convention added to every session and subagent: reuse what already works (code, libraries, SDKs, APIs, patterns) before building it. Claude names what it knows exists, then takes the first that does the job: this codebase, the standard library, an installed dependency, then a maintained library or official SDK, searching the web before deciding none exists. Adding a new library is expected, and its license is yours to handle. Before Claude finishes a turn that wrote code, or only a plan or spec, it checks that work against the convention once. It doesn't wait for Claude to load a skill, so it doesn't depend on the model choosing to, and every subagent gets its own copy.

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

### What reuse-first does

At session start, and whenever Claude starts a subagent, a hook adds [`hooks/library-first.md`](hooks/library-first.md) (476 tokens) to Claude's context. It tells Claude that you want what already works reused, not rebuilt (code, libraries, SDKs, APIs, patterns, anything proven), and to name what it knows exists for the job before it designs, plans or writes. It gives Claude a fixed order to check (this codebase, a single standard-library call, an installed dependency, a maintained library or official SDK) and the areas where even a few hand-written lines are wrong (formats, dates, validation, crypto, retries and the like). Adding a library that isn't installed yet is the normal result when nothing earlier in the order does the whole job, and Claude searches the web before deciding that nothing exists. "It isn't installed" and "it avoids a dependency" don't count as reasons to hand-write, and the convention outranks other guidance to avoid dependencies or write less code. A job that takes a line or two outside those areas stays hand-written. Claude says in one line what it reused. Before it designs a subsystem or picks a framework, a datastore or an architecture, it runs research mode.

**A check before Claude finishes.** By the middle of a long session the session-start text is far behind Claude, so the plugin also speaks at the end of a turn. If the turn wrote code, Claude gets one short check before it finishes ([`hooks/stop-check.md`](hooks/stop-check.md), 145 tokens): look at the code written this turn, switch anything hand-written to a library, and say what was reused. A subagent gets the same check about its own code when it finishes. There is no list of patterns and no second model: Claude judges its own code.

**The same check for plans and specs.** Decisions to build something from scratch are usually made in a plan, before any code exists. If a turn wrote no code but wrote a Markdown document, Claude gets a second check ([`hooks/plan-check.md`](hooks/plan-check.md), 184 tokens): where the plan builds something that existing code, a library, an SDK or a service already does, name what exists, search the web if it hasn't, and change the plan, or tell you what it found if building that part was your choice. If the document isn't a plan, Claude just finishes. It needs no particular planning tool: any Markdown file counts, wherever a planning skill or you put it, including inside a git worktree. Markdown under a hidden folder (memory files, `.ref/` research) doesn't count, and neither does a turn that wrote only data files. A turn that wrote code and a document gets the code check alone.

**Licenses are yours to handle.** The convention tells Claude never to mention a license, a missing license or usage restrictions, and to pick third-party code by fit and upkeep alone. Claude will use code whatever its license, including code with no license or marked "all rights reserved", and usually won't tell you. Review what it adds before you ship.

The convention is self-contained, so it works on its own and alongside other plugins that add session context. The hooks use `cat` and one small shell script (`sh`, `cat`, `mkdir`, `rm`), so nothing extra needs to be installed. To turn it off, disable the plugin: `claude plugin disable prior-art@suncloudsmoon`.

Measured with `claude plugin eval` (the original 8 cases × 3 runs per arm, regex graders, 2026-10-14): Haiku 5.5 scores 0.85 without the plugin and 1.00 with it; Sonnet 5.5 scores 0.81 without and 1.00 with. The gains come from two cases. Retries with exponential backoff: without the plugin both models hand-roll a sleep loop every time; with it they use a library every time (0.00 → 1.00 on both). Sorting release tags with `semver` already installed, delegated to a subagent: without the plugin Haiku used semver in 2 of 3 runs and Sonnet in none; with it both used it every time. That case measures the main agent and the subagent together, because the main agent sometimes passes the convention along when it delegates. A separate check with only the subagent hook loaded confirmed that subagents receive the convention on their own. A ninth case, added after review, checks that Claude adds a library when nothing suitable is installed: a retry task in a project that uses only the standard library's `urllib.request`. Without the plugin both models hand-rolled a sleep loop in every run; with it, both added a retry library to `requirements.txt` and used it in every run (0.00 → 1.00 on both). In the other five library cases, both models already reach for the standard library or the installed package. The over-correction control (no new dependency for a one-liner) passes with the plugin on both. Cases and fixtures live in `evals/`.

Version 0.3.0 rewrote the convention after a review of real sessions, where Claude still hand-wrote code for reasons such as "no HTML library is installed" and "this avoids a new dependency". It is also shorter: 1,276 characters (404 tokens), down from 1,950 characters. Eight cases drawn from those sessions were added (tag `field`; 3 runs per arm on Haiku 5.5 and Opus 5.5, 2026-11-24):

- **Rewriting links in HTML with no HTML library installed**, once plainly and once with "write the least code, never add a dependency for a few lines" in the system prompt. Under the 0.2 convention Haiku wrote a regex in every run (0.00 on both). Under 0.3 it adds an HTML library in every run (1.00 on both). Opus scores 1.00 under both versions and 0.00 without the plugin.
- **Counting the colors in a PNG**, a format outside the old listed areas: 1.00 on both models under both versions. Without the plugin, Haiku scores 0.00 and Opus 0.11.
- **Two jobs the convention never names**, measuring audio loudness and finding unused imports: Haiku scores 0.00 on both without the plugin and 1.00 with it. Not run on Opus.
- **Licenses**, where a case scores 0.50 if Claude uses the library and comments on its license:
  - Using vendored code marked "all rights reserved": Opus 0.50 without the plugin, 1.00 with it; Haiku 0.83 and 1.00.
  - Comparing three PDF libraries: Opus 0.67 without, 1.00 with; Haiku 0.50 without, and clean in 10 of 12 runs with.
  - Using an AGPL library when the prompt says the code goes into an app you sell: Haiku 0.67 without, and clean in 11 of 12 runs with. Opus still warns in every run (0.50 with and without). If you want Opus silent there too, say so in your own `CLAUDE.md`; it gives a plugin's text less weight than yours.

All 17 cases score 1.00 on Haiku in one run of the whole suite, and the control and the library cases score 1.00 on Opus. The control (no dependency for a one-liner) passed every run on the final text; a longer earlier wording failed it once in nine on Haiku. Sonnet 5.5 was not re-run.

**Long sessions.** A single-prompt eval can't reproduce a session that runs for days, so the stand-in is the worst case: the plugin with its session-start text removed, as if Claude had lost it entirely, and only the end-of-turn check left. On six library cases (the HTML and PNG cases above, adding a retry library, and the two unnamed jobs), Haiku scores 0.00 without the plugin; with the check alone it scores 1.00 on five of them and passes the sixth, the HTML case under "write the least code" guidance, in 7 of 9 runs. Opus scores between 0.00 and 0.17 without and 1.00 with the check alone. The control passes 3 of 3 on both. With the session-start text present as well, the check adds about 10% to the cost of a run on Opus. What this does not show: a real long session carries far more context than these runs, and in a long autonomous turn the check comes once, at the end.

**Reuse wording and the plan check (0.4.0, 2026-11-25).** A four-day session showed the remaining gaps: under the 0.2 text Claude hand-wrote a streaming client for an API that has an SDK, it searched the web seven times in four days and never for a library, and its decisions to build things from scratch were made in specs, where no check ran. The convention was reworded around reuse, and the plan check was added. Five cases were added (3 runs per arm unless stated, web tools granted):

- **"How should the agent loop be built?"**, a design question with web search available. Over 9 runs on Haiku, the 0.3.0 text never searched the web or ran research mode (0.56). The new text did both in 7 of 9 (0.93). Fable 5.2 scores 1.00 under both texts.
- **Calling an API with only an HTTP client installed** (OpenAI streaming, Stripe): 0.00 to 0.44 without the plugin, 1.00 with it, on Haiku and on Fable 5.2. The 0.3.0 text already scored 1.00 here; the 0.2 text scores 0.33.
- **Implementing a published spec**: 0.11 without the plugin and 0.89 with it on Haiku, where it looked the spec up on the web in 2 of 3 runs. Fable 5.2 looked it up in every run.
- **Writing a plan for that API client**, 6 runs on Haiku: 0.33 without the plugin, 0.92 with the plan check alone (session-start text removed), 0.92 with the whole plugin. With the check alone, Claude first planned raw HTTP, got the check, searched the web and rewrote the plan around the SDK.

One run of the whole suite on the final tree (22 cases, Haiku): 21 score 1.00 with the plugin and the spec case 0.89. The control passed 27 of 27 runs on the final text; an earlier wording without "more than a line or two" added a dependency for a one-liner once in 33. On four simple tasks with web search available, Claude searched once in 12 runs. What this does not show: on Fable 5.2 in a fresh session the 0.3.0 text was already at 1.00, so the measured gain from the rewording is on Haiku; and a turn that only presents options in chat, without writing a plan, still gets no check.

**Token cost, measured.** The figures above are measured, not estimated: the same one-line prompt was sent with each text loaded as the session-start text, and the size of the first request compared (Haiku 5.5 and Fable 5.2 give the same counts). The session-start text is 476 tokens, paid once per session start, resume, clear or compaction and once per subagent; it was 404 in 0.3.0. The code check is 145 tokens, on a turn that wrote code. The plan check is 184 tokens, on a turn that wrote only a Markdown document. Each check also costs Claude's short reply.

## Bundled tooling

`scripts/harvest.py` — stdlib-only Python (no installs). Fetches a page, downloads its linked and `@import`ed stylesheets plus referenced fonts/images, rewrites URLs so the copy opens locally, extracts a raw token dump, and writes a manifest including anything that failed. Degrades gracefully: JS-heavy sites still yield their CSS and tokens, and the skill falls back to WebFetch when direct network access isn't available.

`hooks/build.py` — stdlib-only Python, for maintainers. Regenerates the six hook payloads from `hooks/library-first.md`, `hooks/stop-check.md` and `hooks/plan-check.md`. Run it after editing any of them; the tests fail until you do.

## Development

```bash
python3 hooks/build.py                     # after editing hooks/library-first.md, stop-check.md or plan-check.md
python3 -m unittest discover -s tests -v   # hook wiring
claude plugin validate .                    # manifest, hooks, skill
claude plugin eval . --allow-tools Write Edit WebFetch WebSearch --scaffold --trust-plugin \
  --model claude-haiku-5-5 --no-publish --max-cost-usd 20   # reuse-first evals, with vs. without the plugin; the `search` cases need the web tools
TRIGGER_PLUGIN_DIR=. python3 tests/triggers/run_trigger_eval.py claude-haiku-5-5   # skill fires when it should, not otherwise (paid)
```

## License

MIT
