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
- **Composes with superpowers and ponytail.** No contradiction with ponytail's ladder (codebase → stdlib → installed dependency → minimal code, "never add a dependency for a few lines"). Routine checks don't route into superpowers-style heavy flows. Its context stacks with theirs (~800 + ~700 tokens, measured), so it stays the smallest of the three.
- **No new runtime.** The plugin already needs `python3` for `harvest.py`; nothing else gets added.

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
| `hooks/hooks.json` | new | `SessionStart` (matcher `startup\|resume\|clear\|compact`) and `SubagentStart` (no matcher, so every agent type) each run `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/inject.py" <event>`, timeout 10 s. Auto-loaded from the plugin root, so no manifest key. |
| `hooks/inject.py` | new, ~8 lines | Reads `library-first.md`, prints `{"hookSpecificOutput": {"hookEventName": <event>, "additionalContext": <text>}}`. JSON is required because `SubagentStart` ignores plain stdout. Only this one field is emitted, so nothing is duplicated when combined with other plugins' output. Doesn't read stdin. |
| `hooks/library-first.md` | new, ~475 tokens | The convention text. Single source of truth. |
| `skills/prior-art/SKILL.md` | edit | Description: replace "is about to build something where proven examples surely exist" with hard-to-undo choices, and say routine library checks are handled inline by the convention. Stays under the 1,536-character listing cap (currently 1,045). Body: a short "Always on" section on where research mode stops and the convention takes over. |
| `README.md` | edit | Document the always-on convention: what it does, ~475 tokens per session and per subagent, needs `python3`, how to turn it off (disable the plugin). |
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
| ponytail | Same order plus one rung (well-known library for >~20 lines or a listed area). Both forbid adding a dependency for trivial code. |
| superpowers | Its rule to load any skill that might apply would make prior-art fire on every helper. The narrowed description, plus the convention saying routine checks happen inline, keep research mode for hard-to-undo choices. |
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

Run each model with the built-in with/without-plugin arms:

```bash
for m in claude-haiku-5-5 claude-sonnet-5-5; do
  claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
    --model "$m" --output-dir "evals/results/$m" --no-publish --max-cost-usd 20
done
```

Bash is deliberately not granted. Without network access, a `pip install` or `npm install` would fail inside the sandbox and could push the model back to hand-rolling, which would measure the sandbox instead of the decision.

`--max-cost-usd 20` is a ceiling per model (8 cases × 3 runs × 2 arms = 48 runs), not an estimate.

Before the evals: `claude plugin validate .`, run `inject.py` for both events and check that the JSON parses and the text is under the 10,000-character cap, and do one live session with `--plugin-dir .` to confirm the context arrives.

## Out of scope

- **A per-prompt reminder (`UserPromptSubmit`) for long sessions.** Single-prompt evals can't measure it, so it's added only if the convention is seen fading.
- **Option C (write-time check).**
- **An opt-out switch.** Disabling the plugin does that.
- **A Codex port.**
- **Updating the separate `plugins` marketplace repo's description.**

## Risks

- **No `python3` on PATH:** the hook errors without blocking and the convention silently doesn't load.
- **Managed hook restrictions:** `allowManagedHooksOnly` in managed settings blocks plugin hooks.
- **Prompt-injection defenses:** if Haiku treats the attributed text as an injection anyway, the with-plugin scores will show it, and the wording changes before shipping.
- **Over-correction (unneeded dependencies):** guarded by the control case and the "one line" rule.
