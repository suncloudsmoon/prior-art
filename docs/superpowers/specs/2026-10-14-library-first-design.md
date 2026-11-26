# Library-first convention — design

| | |
|---|---|
| Date | 2026-10-14 |
| Status | Draft for review |
| Plugin version | 0.1.0 → 0.2.0 |
| Sources | Claude Code docs: [hooks](https://code.claude.com/docs/en/hooks), [plugin components](https://code.claude.com/docs/en/plugins/components), [manifest](https://code.claude.com/docs/en/plugins/manifest-reference), [skills](https://code.claude.com/docs/en/skills), [plugin evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-10-14, Claude Code 2.1.299); installed ponytail 5.2.0 and superpowers 6.4.1 hooks |

## Goal

Claude reaches for an existing solution (this codebase, the standard library, an installed dependency, then a well-known library) before hand-rolling code for an already-solved problem. It has to hold on cheaper models (Haiku, Sonnet) and inside subagents, not just on Opus in the main thread.

**Success:** on each of `claude-haiku-5-5` and `claude-sonnet-5-5`, the eval suite below scores at least 0.8 with the plugin, has a mean Δ above 0 (with plugin minus without), and scores 1.0 with the plugin on the over-correction control.

## Constraints

- **Standalone.** Works with no other plugin installed. The injected text names no other plugin.
- **Composes with superpowers and ponytail.** Follows ponytail's ladder (codebase → stdlib → installed dependency → minimal code) and agrees with its "never add a dependency for a few lines" outside the listed areas. Inside them it deliberately prefers a well-known library (see "Changes during implementation"). Routine checks don't route into superpowers-style heavy flows. Its context stacks with theirs (~800 + ~700 tokens, measured), so it stays the smallest of the three.
- **No new runtime.** The hooks only `cat` pre-built JSON, so they need nothing beyond the shell Claude Code already uses (`sh`, Git Bash or PowerShell).

## Why the plugin can't do this today

1. **The skill only acts when Claude loads it.** Hand-rolling happens when prior art isn't on Claude's mind, which is exactly when it won't decide to load a skill. Weaker models load skills on their own less often.
2. **The trigger text can vanish.** When the skill listing overflows its budget (1% of the context window), Claude Code drops descriptions starting with the least-invoked skills (skills docs, "Skill descriptions are cut short").
3. **Research mode is too heavy for this.** It stops, writes a findings doc, and waits. That fits "which datastore?", not "is there a library for this?"
4. **No other always-on channel exists.** A plugin-root `CLAUDE.md` isn't loaded (manifest docs, "Standard layout"). Hooks are the only plugin component that puts text in front of every session.

## Options considered

| Option | Verdict |
|---|---|
| A. Skill-only: sharper description plus a library-check section | Rejected. Still depends on Claude choosing to load the skill, which is the failure. |
| **B. Hook-injected convention into every session and subagent** | **Chosen.** Doesn't depend on the model, reaches subagents, same pattern as superpowers and ponytail. |
| C. B plus a PostToolUse check on Write/Edit for hand-rolled signatures | Deferred. Strongest nudge, but per-language regexes, false positives, and blind to files written through Bash (hooks docs, PostToolUse). Revisit only if B misses the bar. |

## Components

| File | Change | Responsibility |
|---|---|---|
| `hooks/hooks.json` | new | `SessionStart` (matcher `startup\|resume\|clear\|compact`) and `SubagentStart` (no matcher, so every agent type) each run `cat "${CLAUDE_PLUGIN_ROOT}/hooks/<event>.json"` (`session-start.json`, `subagent-start.json`), timeout 10 s. Auto-loaded from the plugin root, so no manifest key. |
| `hooks/build.py`, `hooks/session-start.json`, `hooks/subagent-start.json` | new | `build.py` (maintainer tool, standard library only) writes each payload as ASCII JSON: `{"hookSpecificOutput": {"hookEventName": <event>, "additionalContext": <library-first.md>}}`. JSON is required because `SubagentStart` ignores plain stdout. Only this one field is emitted, so nothing is duplicated when combined with other plugins' output. The tests fail if a payload is stale. Replaced the original `inject.py` after review: a hook that needs `python3` errors visibly on every start where `python3` doesn't resolve (Windows without Python, an uninstalled pyenv version). |
| `hooks/library-first.md` | new, ~475 tokens | The convention text. Single source of truth. |
| `skills/prior-art/SKILL.md` | unchanged | The planned description narrowing was dropped during implementation; see "Changes during implementation". |
| `README.md` | edit | Document the always-on convention: what it does, ~475 tokens per session and per subagent, how to turn it off (disable the plugin). |
| `.claude-plugin/plugin.json` | edit | Version 0.2.0, description, keywords. |
| `.gitignore` | edit | Add `evals/results/`. |
| `evals/` | new | Eval suite described below. |

### Why `resume` is in the matcher

A resumed session's transcript may or may not carry the earlier injection. A duplicate costs ~475 tokens, and a missing one loses the rule, so the hook runs on resume too (ponytail makes the same choice). `fork` is left out because a fork inherits the parent's conversation.

## The convention text

Written for cheaper models:

- **Attributed facts, not commands.** The hooks docs warn that injected text "framed as out-of-band system commands can trigger Claude's prompt-injection defenses".
- **A fixed order and a number.** The steps and the ~20-line threshold replace judgment calls.
- **Named standard-library examples.**
- **A concrete list of areas.** The trigger is a category match, not taste.
- **A one-line disclosure.** It makes the check happen and makes it gradeable.

Draft (final wording may tighten during implementation):

```markdown
## Library-first convention (prior-art plugin)

The user installed the prior-art plugin. Its convention for code written in this session: before hand-writing code for a problem that is already solved, reuse an existing solution, taking the first that fits.

1. This codebase: an existing helper or pattern. Search before writing.
2. The standard library or platform. Python: argparse, csv, json, tomllib, datetime + zoneinfo, secrets, pathlib, urllib.parse, difflib, functools.cache, itertools, dataclasses, logging. JS/TS: URL, URLSearchParams, structuredClone, Intl (dates, numbers, plurals), crypto.randomUUID, fetch, AbortController, util.parseArgs.
3. A dependency that is already installed. The manifest (package.json, pyproject.toml, requirements*.txt, go.mod, Cargo.toml) lists what is available; read it before writing.
4. A well-known, maintained library, when a hand-written version would run past ~20 lines or falls in a listed area. Adding it is expected: add it to the manifest and name it in one line.
5. Hand-written code, kept small, only when none of the above fits.

Listed areas, where the check always applies: parsing or writing a format (CSV, JSON, YAML, TOML, XML, HTML, Markdown, URLs, query strings); dates, times and time zones; CLI arguments; validating emails, URLs or UUIDs; parsing or comparing versions; crypto, hashing, random tokens and passwords; auth and sessions; retries, backoff and rate limits; HTTP clients; concurrency and queues; caching; diffing and fuzzy matching; Unicode and slugs; deep clone, merge or equality; money and currency formatting.

No new dependency for what the standard library or one line already does.
After writing code in a listed area, the reply names what was reused in one line, e.g. "Used argparse instead of parsing sys.argv by hand."
Hard-to-undo choices (a framework, a datastore, an architecture) go through the prior-art skill's research mode instead of being picked inline.
```

**New-dependency policy:** step 4 adds the library and names it, without asking first. Subagents can't stop to ask, and Claude Code's permission prompt on the install command remains the user's veto.

## How it composes

| With | Interaction |
|---|---|
| ponytail | Same order plus one rung (well-known library for >~20 lines or a listed area). Outside the listed areas both forbid adding a dependency for a few lines. Inside them prior-art deliberately prefers the library, so with both installed they disagree only there. |
| superpowers | Feared: its rule to load any skill that might apply would make prior-art's research mode fire on routine helpers. Measured: it doesn't (see "Changes during implementation"), so the skill description stays as it was. The convention routes only hard-to-undo choices to research mode. |
| any plugin | Hook outputs are combined. Only `hookSpecificOutput.additionalContext` is emitted, wrapped under its own heading. |

## Verification

A `claude plugin eval` suite in `evals/`. Each case has:

- A `prompt.md` with a plain user-style request and `allowed_tools: [Read, Glob, Grep, Skill]`, plus `Agent` for the subagent case. `Skill` stays available so a run that wrongly detours into research mode shows up as a failed case.
- A `case.yaml` with a `scaffold_script` that writes a tiny fixture project.
- Regex graders on file contents (`target: {source: file, path: …}`). There are no LLM judges, so grading costs nothing and doesn't vary.

| Case | Fixture | Pass condition |
|---|---|---|
| `js-deep-copy` | `settings.js` mutating a nested config | `structuredClone`; no `JSON.parse(JSON.stringify` |
| `py-csv-quoted` | `orders.csv` with quoted commas | `import csv`; no `.split(",")` |
| `py-timezone` | UTC timestamps, show in New York time | `zoneinfo` |
| `js-currency` | prices shown to German users in euros | `Intl.NumberFormat` |
| `ts-validate-installed` | `package.json` with zod | imports `zod` |
| `py-retry` | `requirements.txt` with requests only | `tenacity`, `backoff`, `stamina` or urllib3 `Retry`; no `time.sleep` |
| `subagent-semver-installed` | `package.json` with semver; sort release tags, asked to delegate | imports `semver`; `Agent` tool used |
| `control-no-new-dep` | `package.json` with empty dependencies, "capitalize each word" | dependencies still empty |
| `py-retry-new-dep` (added after review) | `requirements.txt` with `click` only; client uses stdlib `urllib.request` | imports `tenacity`, `backoff`, `stamina` or `urllib3`; `requirements.txt` lists it; no `sleep(` |

Run each model with the built-in with/without-plugin arms:

```bash
for m in claude-haiku-5-5 claude-sonnet-5-5; do
  claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
    --model "$m" --output-dir "evals/results/$m" --no-publish --max-cost-usd 20
done
```

Bash is deliberately not granted. Without network access, a `pip install` or `npm install` would fail inside the sandbox and could push the model back to hand-rolling, which would measure the sandbox instead of the decision.

`--max-cost-usd 20` is a ceiling per model (8 cases × 3 runs × 2 arms = 48 runs), not an estimate.

Before the evals: `claude plugin validate .`, run both hook commands and check that the JSON parses and the text is under the 10,000-character cap, and do one live session with `--plugin-dir .` to confirm the context arrives.

## Out of scope

- **A per-prompt reminder (`UserPromptSubmit`) for long sessions.** Single-prompt evals can't measure it, so it's added only if the convention is seen fading.
- **Option C (write-time check).**
- **An opt-out switch.** Disabling the plugin does that.
- **A Codex port.**
- **Updating the separate `plugins` marketplace repo's description.**

## Changes during implementation

**The skill description is unchanged (2026-10-14).** Before editing it, a control test checked the feared failure:

- **Setup:** an isolated session with superpowers 6.4.1, ponytail 5.2.0 and this plugin (convention hooks active, original description), on `claude-haiku-5-5`.
- **Prompt:** "In utils.py, add a function that retries a flaky callable with exponential backoff." Turn cap 4, 5 runs.
- **Result:** prior-art was invoked in 0 of 5 runs. Four runs invoked `superpowers:test-driven-development`, one invoked no skill, and all five went straight to the task.

With no failure in the control, there was nothing for the narrowing to fix, so it wasn't written. If research-mode detours show up later, the eval suite (which allows the `Skill` tool) surfaces them, and the fix is a one-line description edit.

**In listed areas, a library beats a few lines (after review, 2026-10-14).** Step 4 adds a well-known library for anything in a listed area, even when a few handwritten lines would do. That contradicts ponytail's "never add a dependency for a few lines" inside the listed areas, which the original constraint missed. The convention wins there on purpose:

- The user asked for more library use.
- These areas are where short hand-rolled code hides bugs: retry semantics, version ordering, quoting.

The `py-retry-new-dep` case checks the outcome. With no HTTP library installed, the model should add a retry library to the manifest and use it.

Result (3 runs per arm on each model): without the plugin, Haiku 5.5 and Sonnet 5.5 hand-rolled a sleep loop in every run; with it, both added and used a retry library in every run (0.00 → 1.00 on both).

## Changes after field use (2026-11-24, version 0.3.0)

The convention text above is the 0.2 text. The current text is `hooks/library-first.md`.

**What the session logs showed.** The hook fired in 47 real sessions and 66 of their subagents (mostly Opus 5.5, some lasting days). It was re-injected after every compaction, so delivery was not the problem. The model cited the convention in three decisions and reused existing work each time (an official client library, `cryptography`, a helper already in the app). More often it hand-wrote, with these reasons in its own words:

| Reason given | Example from the logs | What 0.3 says |
|---|---|---|
| Nothing is installed | "`responses` and `requests_mock` aren't installed, so I'm leaning toward a custom adapter" | "Not installed" is the reason for step 4. |
| Avoiding a dependency is a goal | "prefer no new dependency if performance is equal"; a plan with the constraint "no new dependencies" that the user never asked for | The user wants the dependency. This outranks any guidance to avoid dependencies or write less code. |
| The standard library could do it | "read the PNG's header and image data directly … instead of pulling in PIL"; "HTMLParser in about thirty lines" | Step 2 is a single call. Regex, a parser subclass or a sleep loop on top of the standard library is step 5. |
| License | re-implementing a cloned repo "because their MIT license allows adapting it with attribution"; license columns in comparisons | Never mention a license, a missing one or usage restrictions. |

The author had told the model not to worry about licenses, more than once.

**Requirements the user set on 2026-11-24.**

- Stronger push toward third-party libraries.
- Licenses are the user's to handle. That covers code they sell and code with no license or a restrictive one. Claude says nothing about them.
- The always-on text uses as few tokens as possible.

**What changed.**

- Step 4 no longer has a threshold (20 lines or a listed area). A library that isn't installed is the normal result when steps 1-3 fall short.
- The convention outranks other session guidance to avoid dependencies or write less code, everywhere and not only in the listed areas. This extends the 2026-10-14 decision.
- The long list of areas is gone. Five examples remain ("formats, dates, validation, crypto, retries and the like"), next to the sentence that regex, a parser subclass or a sleep loop over the standard library counts as hand-written.
- The standard-library and platform name lists (argparse, csv, structuredClone and the rest) are gone. No case depends on them: the four standard-library cases score 1.00 on Haiku without the plugin.
- "No new dependency for what the standard library or one line already does" is gone, because models quoted it as a reason to hand-write. Step 5 keeps the one-line exception, and the control case still passes.
- Licenses: one paragraph, as above. The README tells users the review is theirs.

**Size.** About 310 tokens (1,276 characters), down from about 475 (1,950 characters).

**Wordings tried and dropped.**

- A longer version (about 820 tokens) with one bullet per ruled-out reason. It passed the same cases, so the extra tokens bought nothing.
- Two shorter versions (about 320 and 340 tokens). Under the first, Haiku hand-wrote the HTML rewriter in 2 of 3 runs ("standard library only, so no new dependency"). Under the second, with lean-code guidance present, it wrote a regex in 4 of 6 ("a new install for a few lines").
- "Unless asked, don't check, mention or weigh them" for licenses. Haiku named the license in order to say it wasn't weighing it.
- A 390-token version with the full list of areas (file formats, dates and time zones, CLI arguments and a dozen more). It scored the same as the 310-token text on all 17 cases on Haiku and on the field cases on Opus, so the list bought nothing.
- A license paragraph without "they handle licensing themselves … and installed this plugin to stop hearing about it". On Haiku the comparison case stayed clean in 1 of 6 runs, against 4 of 6 with that clause.

**Verification.** Eight cases from the logs (tag `field`), 3 runs per arm. A license case scores 0.50 when Claude uses the library and comments on its license.

| Case | Haiku 5.5: without → with | Opus 5.5: without → with |
|---|---|---|
| `py-html-links-new-dep` | 0.00 → 1.00 (0.2 scored 0.00) | 0.00 → 1.00 (0.2 scored 1.00) |
| `py-html-links-lean-guidance` (lean-code guidance in the system prompt) | 0.00 → 1.00 (0.2 scored 0.00) | 0.00 → 1.00 (0.2 scored 1.00) |
| `py-png-new-dep` | 0.00 → 1.00 (0.2 scored 1.00) | 0.11 → 1.00 (0.2 scored 1.00) |
| `py-loudness-new-dep` (a job the convention never names) | 0.00 → 1.00 | not run |
| `py-unused-imports-new-dep` (a job the convention never names) | 0.00 → 1.00 | not run |
| `py-license-restricted` (vendored code marked "all rights reserved") | 0.83 → 1.00 | 0.50 → 1.00 |
| `py-license-users-call` (compare three PDF libraries) | 0.50 → 0.92 (clean in 10 of 12 runs) | 0.67 → 1.00 |
| `py-license-sold` (AGPL library, "this goes into the app we sell") | 0.67 → 0.96 (clean in 11 of 12 runs) | 0.50 → 0.50 |

Under 0.2, Haiku's failing replies read: "`requirements.txt` has only `requests`, so no HTML library is installed" and "What I reused: `urllib.parse.urljoin` from the standard library, so there is no new dependency". All 17 cases score 1.00 on Haiku in one run of the whole suite on the final tree; the control, the library cases above and `py-retry-new-dep` score 1.00 on Opus. The control passed every run on the final text (6 on Haiku, 3 on Opus); the 390-token wording failed it once in nine on Haiku, by adding a dependency for a one-liner. Sonnet 5.5 was not re-run.

**Not fixed, not measured.**

- `py-license-sold` on Opus. Two wordings were tried. Opus warned in every run and answered one of them: "a plugin you have installed told me not to bring up licenses. I'm raising it anyway because you said this goes into an app you sell." Opus treats the hook as a plugin's voice and the prompt as the user's, so more wording in the hook is unlikely to change it. An instruction in the user's own CLAUDE.md is the place for it.
- `py-license-users-call` on Haiku is not fully reliable: clean in 10 of 12 runs with the final text.
- Opus passed the new library cases under 0.2 in fresh sessions, yet hand-wrote in long ones. Single-prompt evals don't reproduce a real long session. The end-of-turn check below is measured against a stand-in for one.

## End-of-turn check (2026-11-24, version 0.3.0)

**Why.** The session-start text is re-injected after every compaction, but by the time Claude decides to hand-write something it can be a whole context window behind. The user asked for the plugin to hold in long sessions too, with three conditions: no fixed list of patterns ("it's hard for structured rules to work for every case"), no second model called on each write, and as few tokens as possible. They pointed at the completion check in their own persona setup as the shape to copy.

**How it works.**

- A `PostToolUse` hook on `Write|Edit|MultiEdit|NotebookEdit` records that code was written. Prose and data files (`.md`, `.json`, `.yaml` and similar) don't count.
- A `Stop` hook hands Claude `hooks/stop-check.md` once, as `hookSpecificOutput.additionalContext`, if code was written since the last check. Claude Code shows this as hook feedback, not as an error.
- Fixes Claude makes in answer to the check are not checked again. If another plugin's stop hook made Claude write more code, that code is checked.
- A subagent is asked about its own code on `SubagentStop`; the main agent is not asked about it again.
- State is two empty files per session or subagent under `${CLAUDE_PLUGIN_DATA}/wrote`. The script uses shell builtins plus `cat`, `mkdir` and `rm`, so the 2026-10-14 decision to need no interpreter holds.

**Alternatives.** The research is in `.ref/prior-art/plugin-effectiveness.md`.

| Alternative | Outcome |
|---|---|
| Regex pattern warnings at write time, as in Anthropic's security-guidance | Not built. Most real misses (a custom media format, a hand-built loudness filter) have no pattern to name. |
| A prompt hook: a small model judges each write | Built and measured on Haiku with the session-start text removed: 1.00 on six of seven cases, 0.67 on the seventh. Removed at the user's request: it calls a model on every write. |
| A one-line reminder on every prompt, as in caveman | Not built. It adds nothing during a long autonomous turn and costs tokens on every prompt. |
| A note after the first write to each file | Not built. The user chose the end-of-turn check. |

**Wording.** The first version ended "or say in one line why none fits". With the session-start text removed, Haiku took that way out: "`bs4` or `lxml` would be a new dependency for a six-line rewrite … I kept the regex." It scored 0.00 to 0.67 on four of the six library cases. The final version says the user wants the dependency and names the only two reasons to keep hand-written code. Three shorter versions (220, 310 and 388 characters against 490) were tried to save tokens. Each dropped or compressed the sentence about "not installed" and "a new dependency", and each did worse on the HTML cases: at six runs, the 388-character version passed 8 of 12 against 10 of 12.

**Verification.** The stand-in for a long session is the worst case: the plugin with its session-start hooks removed, as if Claude had lost the convention entirely, leaving only the check. 3 runs per cell.

| Case | Haiku 5.5: no plugin → check only | Opus 5.5: no plugin → check only |
|---|---|---|
| `py-html-links-new-dep` | 0.00 → 1.00 | 0.00 → 1.00 |
| `py-html-links-lean-guidance` | 0.00 → 0.78 (7 of 9 runs) | 0.00 → 1.00 |
| `py-png-new-dep` | 0.00 → 1.00 | 0.11 → 1.00 |
| `py-retry-new-dep` | 0.00 → 1.00 | 0.00 → 1.00 |
| `py-loudness-new-dep` | 0.00 → 1.00 | 0.17 → 1.00 |
| `py-unused-imports-new-dep` | 0.00 → 1.00 | 0.00 → 1.00 |
| `control-no-new-dep` | 1.00 → 1.00 | not run → 1.00 |

With the session-start text and the check together, all 17 cases score 1.00 on Haiku in one run of the whole suite, and the seven cases above score 1.00 on Opus.

**Cost.** The check is about 120 tokens, added only to a turn that wrote code, plus Claude's short answer. Measured on the same cases with and without it: 10% more per run on Opus, 7% more on Haiku. Skipping the session-start text for subagents that never write code was considered and dropped: 58 of the 66 subagents in the logs were general-purpose ones that do.

**What this does not show.**

- A real long session carries far more context than these runs. The stand-in removes the convention; it does not add a day of history.
- In a long autonomous turn the check comes once, at the end, over everything written in that turn. Replacing code that later code was built on costs more than catching it at the time.
- Code written through a shell command (a heredoc, `sed`) is not seen by the write hook.

## Reuse wording and the plan check (2026-11-25, version 0.4.0)

**What the session log showed.** One four-day session in another project ran 0.2.2 for three days and 0.3.0 for the last.

- Under 0.2.2 it hand-wrote a streaming client for the OpenAI API on top of an installed HTTP client, chose to write its own agent loop from a list of options written from memory, and recorded "our own adapters are the default, and a library is the exception".
- It made seven web searches in four days, none of them for a library, and ran research mode once.
- After 0.3.0 loaded, the end-of-turn check fired nine times and led to three swaps to libraries.
- The build-it-ourselves decisions were made in turns that presented options or wrote a spec. Those turns wrote no code, so they got no check.

**Requirements the user set on 2026-11-25.**

- Emphasize reuse, not only libraries: "APIs, patterns and others that just work", with no fixed list of what counts.
- Claude should look for what exists: search the web, and use what it already knows.
- Check plans and specs at the end of a turn too. It must work with planning skills from other plugins and without them.

**What changed in the session-start text.** It is now headed "Reuse-first".

- The opening names what to reuse ("code, libraries, SDKs, APIs, patterns, anything proven") and adds "Before you design, plan or write more than a line or two, name what exists for the job; you know more than you use."
- Step 4 reads "A maintained library or official SDK" and ends "Search the web before deciding none exists."
- The last line is an instruction: "Before designing a subsystem or picking a framework, datastore or architecture, run the prior-art skill's research mode."
- The file is still `hooks/library-first.md`.

**Size.** 476 tokens (1,488 characters), up from 404. Token figures in the earlier sections were estimated from character counts at about 4.1 characters per token, which runs about a quarter low. These are measured: the same one-line prompt was sent with each text loaded as the session-start text, and the size of the first request compared. Haiku 5.5 and Fable 5.2 give the same counts. The 0.3.0 text is 404 tokens (the earlier sections say about 310), the code check 145 (they say about 120) and the plan check 184.

**Wordings tried and dropped.**

- Two longer ones (1,567 and 1,545 characters), which added "raw HTTP to an API that has an SDK" and "reference implementation of an API or spec". They scored the same as the final text, so the extra words bought nothing. 0.3.0 already scores 1.00 on the API cases.
- A shorter one (1,400 characters) without the sentence about naming what exists: 0.58 on the design case on Haiku in 3 runs, against 0.93 for the texts that have it.
- The final text without "more than a line or two" (1,464 characters). It added a dependency for a one-line job once in 33 runs of the control. The final text did so in none of 27, and 0.3.0 in none of 15.

**The plan check.** `hooks/plan-check.md`, 184 tokens, delivered the same way as the code check.

- The write hook records a Markdown file (`.md`, `.mdx`) as a document. Markdown under a hidden folder doesn't count: that is a tool's own notes, such as memory files and `.ref/` research. The path is read from the project root, and from inside a worktree, so a worktree under a hidden folder still counts.
- At the end of a turn, written code gets the code check. A turn that wrote only a document gets the plan check. A turn that wrote both gets the code check alone, so ticking off steps in a plan while implementing it doesn't re-open the plan.
- The check ends "If the document is not a plan or design, just finish", so Claude decides whether a README edit is a plan. There is no list of folder or file names.
- It names no other plugin. A planning skill that writes its plan to a Markdown file gets the check because of the file, not because of the skill.

**Alternatives for the plan check.**

| Alternative | Outcome |
|---|---|
| Fire only for paths that contain words such as `plan`, `spec` or `design` | Not built. A fixed list misses documents named any other way, and the user had refused fixed rules for the code check for the same reason. |
| Fire only when a document is created, not when it is edited | Not built. In the session log a spec was created before most of its decisions were made. |
| Fire on every turn that ends | Not built. It costs tokens on every turn. |

In the four-day log the rule as built would have fired on five turns, all of them specs or plans, and skipped four turns that wrote only memory files.

**Verification.** 3 runs per cell unless stated, web tools granted. Scores are with the plugin; "none" is without it.

| Case | Haiku 5.5: none | Haiku: 0.3.0 | Haiku: final text | Fable 5.2: 0.3.0 | Fable 5.2: new text |
|---|---|---|---|---|---|
| `design-agent-loop-search` (how should the agent loop be built) | 0.33 to 0.56 | 0.56 over 9 runs; web search and research mode in 0 of 9 | 0.93 over 9 runs; web search and research mode in 7 of 9 | 1.00 | 1.00 |
| `py-skills-spec-search` (implement a published spec) | 0.00 to 0.11 | 0.78, looked it up in 1 of 3 | 0.89, looked it up in 2 of 3 | looked it up in 3 of 3 | 1.00 |
| `py-openai-stream-new-dep` | 0.00 to 0.44 | 1.00 | 1.00 | 1.00 (0.00 without) | not run |
| `py-stripe-invoices-new-dep` | 0.00 to 0.22 | 1.00 | 1.00 | 1.00 (0.00 without) | not run |

- The 0.2.2 text scores 0.33 on both API cases on Haiku, which matches what the session did under it.
- The Fable runs of the new text used the 1,464-character wording, five words short of the final one.
- Skill triggers, in a setup with other plugins installed (26 prompts, 3 runs each, Haiku): all 14 that should fire do, and all 12 that shouldn't don't. The agent-loop design prompt fires research mode in 3 of 3 runs. Under 0.3.0 it fired in 0 of 3.
- Needless searches: on four simple tasks with web search available (the control, two standard-library cases, the retry case), the new text searched once in 12 runs.
- The whole suite on the final tree, one run on Haiku (22 cases, 3 runs each): 21 cases score 1.00 with the plugin and `py-skills-spec-search` scores 0.89. The control passes. Two cases were run again on their own, because the working tree was briefly changed while the suite ran: `js-currency` scored 1.00, and the design case is reported above over its 9 runs.

The plan check, on `plan-openai-stream-check` (write the plan for a streaming OpenAI client, with only an HTTP client installed), 6 runs per cell on Haiku:

| No plugin | Plan check only (session-start text removed) | Whole plugin |
|---|---|---|
| 0.33 | 0.92 | 0.92 |

In the check-only runs Claude first planned raw HTTP ("avoids a new runtime dependency"), got the check, searched the web and rewrote the plan around the SDK. The sixth run switched to a different library instead of the SDK. In the whole-suite run the case scores 0.00 without the plugin and 1.00 with it.

One real session, in a setup where another plugin's planning skill is installed: the skill wrote its plan to a Markdown file under `docs/`, the Stop hook delivered the plan check (623 characters in the debug log), Claude revised the plan, and the next stop was not checked again. A second Stop hook from another plugin fired at the same stop, and Claude answered both.

**What this does not show.**

- On Fable 5.2 in a fresh session 0.3.0 already scores 1.00 on the design and API cases, so the new wording shows no gain there. The gain is on Haiku.
- A turn that only presents options in chat writes nothing and gets no check. The check comes when the choice is written into a plan or spec.
- A plan written through a shell command is not seen by the write hook.
- The plan check was not run on Fable or Opus.
- A first round of runs granted no web tools, and every text looked as if it never searched. Listing `WebSearch` in a case's `prompt.md` is not enough: pass `--allow-tools Write Edit WebFetch WebSearch`.
- A model-judged grader for "looked it up" marked runs that had fetched the specification as failures. It was replaced with a `tool_used` grader.

## Risks

- **Stale payloads:** editing `library-first.md` without running `build.py` ships the old text. The tests catch it.
- **Managed hook restrictions:** `allowManagedHooksOnly` in managed settings blocks plugin hooks.
- **Prompt-injection defenses:** if Haiku treats the attributed text as an injection anyway, the with-plugin scores will show it, and the wording changes before shipping.
- **Over-correction (unneeded dependencies):** guarded by the control case and the "one line" rule.
