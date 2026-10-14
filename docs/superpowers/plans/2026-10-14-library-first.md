# Library-first Convention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Claude (any model, main thread and subagents) reuse the codebase, the standard library, installed dependencies, then well-known libraries before hand-rolling code, by injecting a short convention through plugin hooks.

**Architecture:** `hooks/hooks.json` (auto-loaded) runs `hooks/inject.py` on `SessionStart` and `SubagentStart`. The script prints `hooks/library-first.md` as `hookSpecificOutput.additionalContext`. The skill description is narrowed so research mode isn't triggered for routine library checks. A `claude plugin eval` suite measures the effect with and without the plugin on Haiku 5.5 and Sonnet 5.5.

**Tech Stack:** Claude Code 2.1.299 plugin hooks; Python 3 standard library (`json`, `pathlib`, `unittest`, `subprocess`); `claude plugin eval` with regex and `tool_used` graders.

**Spec:** `docs/superpowers/specs/2026-10-14-library-first-design.md`

## Global Constraints

- The injected text names no other plugin (prior-art is standalone).
- Nothing in the convention contradicts "never add a dependency for a few lines".
- Runtime: `python3` standard library only. No new dependencies anywhere in the plugin.
- Hook stdout is exactly `{"hookSpecificOutput": {"hookEventName": <event>, "additionalContext": <convention>}}`, with no other fields.
- `SessionStart` matcher is `startup|resume|clear|compact`. `SubagentStart` has no matcher. Each hook's `timeout` is `10`.
- `hooks/library-first.md` stays under 10,000 characters (Claude Code's per-string hook-context cap). Target is ~475 tokens.
- The `skills/prior-art/SKILL.md` description is at most 1,536 characters and contains no `: ` (it's an unquoted YAML scalar).
- Plugin version is `0.2.0`.
- Evals run on models `claude-haiku-5-5` and `claude-sonnet-5-5`, with `--max-cost-usd 20` per model and grants `--allow-tools Write Edit` only (no Bash).
- Pass bar, per model: with-plugin suite score ≥ 0.8, mean Δ > 0, and `control-no-new-dep` scores 1.0 with the plugin.
- Work happens on branch `feat/library-first`. Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Plugin installed under a path with spaces** (e.g. `~/Library/Application Support/…`): the hook still runs. Covered by `test_runs_from_spaced_path_with_non_ascii_text` in Task 1.
2. **Hook started from the user's project directory, not the plugin's:** it still finds `library-first.md`. Covered because `run_hook` runs from a temporary project directory in Task 1.
3. **Claude Code writes the hook-input JSON to stdin:** the script ignores it and exits well inside the 10 s timeout. Covered because `run_hook` passes stdin with `timeout=10` in Task 1.
4. **Non-ASCII added to the convention later, or a non-UTF-8 console (Windows cp1252):** the output stays ASCII-only JSON that round-trips the text. Covered by `test_runs_from_spaced_path_with_non_ascii_text` in Task 1.
5. **The convention grows past the context cap**, which would make Claude get a file path instead of the text. Covered by `test_convention_fits_context_cap` in Task 1.

---

### Task 1: Hook injection

**Files:**
- Create: `hooks/library-first.md`
- Create: `hooks/inject.py`
- Create: `hooks/hooks.json`
- Test: `tests/test_plugin.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `python3 hooks/inject.py <EventName>` prints the hook JSON described in Global Constraints.
  - `tests/test_plugin.py` defines `ROOT` (repo root `Path`); Task 2 appends a test class to this file.

- [ ] **Step 1: Branch and commit the design docs**

```bash
git switch -c feat/library-first
git add docs/superpowers
git commit -F - <<'EOF'
docs: library-first convention spec and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_plugin.py`:

```python
"""Checks the hook wiring that injects the library-first convention."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_CAP = 10_000  # Claude Code's per-string limit on hook context


def hook_config(event):
    [entry] = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"][event]
    [hook] = entry["hooks"]
    return entry, hook


def run_hook(event, plugin_root=ROOT):
    """Run the hook command as Claude Code does: via a shell, from the user's project, with hook input on stdin."""
    _, hook = hook_config(event)
    with tempfile.TemporaryDirectory() as project:
        return subprocess.run(
            ["bash", "-c", hook["command"]],
            input=json.dumps({"hook_event_name": event, "cwd": project}),
            capture_output=True, text=True, timeout=10, check=True, cwd=project,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
        ).stdout


def convention(plugin_root=ROOT):
    return (plugin_root / "hooks" / "library-first.md").read_text(encoding="utf-8")


class HookTests(unittest.TestCase):
    def assert_injects(self, stdout, event, plugin_root=ROOT):
        self.assertTrue(stdout.isascii())
        self.assertEqual(json.loads(stdout), {"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": convention(plugin_root)}})

    def test_session_start_injects_convention(self):
        entry, hook = hook_config("SessionStart")
        self.assertEqual(entry["matcher"], "startup|resume|clear|compact")
        self.assertEqual(hook["timeout"], 10)
        self.assert_injects(run_hook("SessionStart"), "SessionStart")

    def test_subagent_start_injects_convention_for_every_agent_type(self):
        entry, hook = hook_config("SubagentStart")
        self.assertNotIn("matcher", entry)
        self.assertEqual(hook["timeout"], 10)
        self.assert_injects(run_hook("SubagentStart"), "SubagentStart")

    def test_convention_fits_context_cap(self):
        self.assertLess(len(convention()), CONTEXT_CAP)

    def test_runs_from_spaced_path_with_non_ascii_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            spaced = Path(tmp) / "plugin root with spaces"
            shutil.copytree(ROOT / "hooks", spaced / "hooks")
            with open(spaced / "hooks" / "library-first.md", "a", encoding="utf-8") as f:
                f.write("Prices like 1.234,50 € — fine.\n")
            self.assert_injects(run_hook("SubagentStart", spaced), "SubagentStart", spaced)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: 4 errors, each `FileNotFoundError: … hooks/hooks.json` (or `hooks/library-first.md` for the cap test).

- [ ] **Step 4: Write the convention**

Create `hooks/library-first.md`:

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

- [ ] **Step 5: Write the emitter**

Create `hooks/inject.py`:

```python
#!/usr/bin/env python3
"""Print the library-first convention as hook context for the event named in argv[1]."""
import json
import sys
from pathlib import Path

convention = (Path(__file__).parent / "library-first.md").read_text(encoding="utf-8")
print(json.dumps({"hookSpecificOutput": {"hookEventName": sys.argv[1], "additionalContext": convention}}))
```

Leave it non-executable, like `harvest.py`: the hook calls it through `python3`.

- [ ] **Step 6: Wire the hooks**

Create `hooks/hooks.json`:

```json
{
  "description": "prior-art: adds the library-first convention to every session and subagent",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/inject.py\" SessionStart",
            "timeout": 10
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/inject.py\" SubagentStart",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 7: Run the tests and confirm they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: `Ran 4 tests` … `OK`.

- [ ] **Step 8: Validate the plugin**

Run: `claude plugin validate .`
Expected: no errors. Warnings unrelated to `hooks/` may be left as they are.

- [ ] **Step 9: Live smoke test (main thread and subagent)**

Run:

```bash
claude -p --plugin-dir . --model claude-haiku-5-5 \
  "Without using tools: does your context contain a section headed 'Library-first convention (prior-art plugin)'? Answer yes or no, then quote its first sentence."
claude -p --plugin-dir . --model claude-haiku-5-5 \
  "Spawn one general-purpose subagent and ask it: does your context contain a section headed 'Library-first convention (prior-art plugin)'? It must answer yes or no and quote that section's first sentence. Report its answer verbatim."
```

Expected: both answer "yes" and quote "The user installed the prior-art plugin."

If the second command answers "no": run `claude --debug -p --plugin-dir . …` and look for the `SubagentStart` hook in the log before changing anything.

- [ ] **Step 10: Commit**

```bash
git add hooks tests
git commit -F - <<'EOF'
feat: inject library-first convention via SessionStart and SubagentStart hooks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 2: Skill description, docs and manifest

**Files:**
- Modify: `skills/prior-art/SKILL.md` (line 3 description; insert a section after line 19)
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.gitignore`
- Test: `tests/test_plugin.py` (append `SkillTests`)

**Interfaces:**
- Consumes: `ROOT` from `tests/test_plugin.py` (Task 1).
- Produces: README section `### What library-first does`, which Task 4 appends a "Measured" line to.

- [ ] **Step 1: Write the failing test**

In `tests/test_plugin.py`, add `import re` to the imports (alphabetical, after `import os`). Then add this class above `if __name__ == "__main__":`:

```python
class SkillTests(unittest.TestCase):
    def test_description_fits_listing_and_leaves_routine_checks_to_the_convention(self):
        text = (ROOT / "skills" / "prior-art" / "SKILL.md").read_text(encoding="utf-8")
        description = re.search(r"^description: (.*)$", text, re.M).group(1)
        self.assertLessEqual(len(description), 1536)  # Claude Code truncates longer listings
        self.assertNotIn(": ", description)  # unquoted YAML scalar
        self.assertIn("library-first convention", description)
        self.assertNotIn("proven examples surely exist", description)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `python3 -m unittest discover -s tests -v`
Expected: `test_description_fits_listing_and_leaves_routine_checks_to_the_convention … FAIL` with `'library-first convention' not found`. The 4 hook tests still pass.

- [ ] **Step 3: Narrow the skill description**

In `skills/prior-art/SKILL.md`, replace this exact text in the `description:` line:

```text
is about to build something where proven examples surely exist, or mentions .ref/, swipe files, competitor teardowns, or not reinventing the wheel. Also use proactively before greenfield UI work when .ref/ is empty.
```

with:

```text
is about to commit to a hard-to-undo choice (architecture, framework, datastore, protocol), or mentions .ref/, swipe files, competitor teardowns, or not reinventing the wheel. Also use proactively before greenfield UI work when .ref/ is empty. Not for routine "is there a library for this?" checks while coding — the plugin's always-on library-first convention handles those inline.
```

The result is 1,207 characters.

- [ ] **Step 4: Add the "Always on" section to the skill body**

In `skills/prior-art/SKILL.md`, insert the following after the line `A single task can need both (e.g. "build a pricing page" → harvest pricing-page UI *and* research pricing-structure patterns).` and before `## Mode 1 — UI harvest`. Keep a blank line on each side.

```markdown
## Always on: the library-first convention

Separately from the two modes, the plugin's hooks add a short library-first convention (`hooks/library-first.md`) to every session and subagent: check this codebase, the standard library, installed dependencies, then a well-known library before hand-writing code. That convention handles routine "is there a library for this?" checks inline, while coding: no findings doc, no pause. Use research mode only when the choice is hard to undo (framework, datastore, architecture) or the user asks how others do it.
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: `Ran 5 tests` … `OK`.

- [ ] **Step 6: Update the README**

In `README.md`:

(a) Replace `It has two modes:` with `It has two modes, plus one always-on convention:`.

(b) After the `- **Research** — …` bullet, add this bullet:

```markdown
- **Library-first (always on)** — a short convention added to every session and subagent: before hand-writing code for an already-solved problem, use this codebase, the standard library, an installed dependency, then a well-known library, in that order. It doesn't wait for Claude to load a skill, so it holds on Haiku and Sonnet and inside subagents.
```

(c) After the `### What research mode produces` section (it ends with "It proposes; you decide what gets built."), add:

```markdown
### What library-first does

At session start, and whenever Claude starts a subagent, a hook adds [`hooks/library-first.md`](hooks/library-first.md) (~475 tokens) to Claude's context. It gives Claude a fixed order to check before writing a helper (this codebase, the standard library, an installed dependency, a well-known library), the areas where hand-rolled code most often goes wrong (parsing formats, dates and time zones, validation, crypto, retries, money and more), and one guardrail: no new dependency for what the standard library or one line already does. When Claude adds a library, it names it in one line. Hard-to-undo choices, such as a framework or a datastore, still go through research mode.

The convention is self-contained, so it works on its own and alongside other plugins that add session context. It needs `python3` on your PATH. To turn it off, disable the plugin: `claude plugin disable prior-art@suncloudsmoon`.
```

(d) In `## Bundled tooling`, after the `scripts/harvest.py` paragraph, add:

```markdown
`hooks/inject.py` — stdlib-only Python. Prints `hooks/library-first.md` as hook context for `SessionStart` and `SubagentStart`.
```

(e) Before `## License`, add:

````markdown
## Development

```bash
python3 -m unittest discover -s tests -v   # hook wiring and skill description
claude plugin validate .                    # manifest, hooks, skill
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
  --model claude-haiku-5-5 --no-publish --max-cost-usd 20   # library-first evals, with vs. without the plugin
```
````

- [ ] **Step 7: Update the manifest and .gitignore**

Replace `.claude-plugin/plugin.json` with:

```json
{
  "name": "prior-art",
  "version": "0.2.0",
  "description": "Study how the best already solved it, then copy what works. An always-on library-first convention steers Claude and its subagents to the standard library, installed dependencies and well-known libraries before hand-rolling code. UI mode harvests reference interfaces (HTML, CSS, design tokens) from excellent brands into a gitignored .ref/ archive with a curated audit; research mode finds 3-5 strong implementations of anything else (architecture, hardware, best-known methods) and presents a copy-this recommendation before building.",
  "author": {
    "name": "suncloudsmoon",
    "url": "https://github.com/suncloudsmoon"
  },
  "homepage": "https://github.com/suncloudsmoon/prior-art",
  "repository": "https://github.com/suncloudsmoon/prior-art",
  "license": "MIT",
  "keywords": ["references", "design", "swipe-file", "research", "prior-art", "design-tokens", "best-known-methods", "library-first", "stdlib"]
}
```

Append `evals/results/` as a new line to `.gitignore`.

- [ ] **Step 8: Validate and re-run the tests**

Run: `claude plugin validate . && python3 -m unittest discover -s tests -v`
Expected: validate reports no errors, and the tests show `Ran 5 tests` … `OK`.

- [ ] **Step 9: Commit**

```bash
git add skills/prior-art/SKILL.md README.md .claude-plugin/plugin.json .gitignore tests/test_plugin.py
git commit -F - <<'EOF'
feat: document library-first convention, narrow research-mode trigger, bump to 0.2.0

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 3: Eval suite

**Files:** create, for each case below, `evals/<case>/case.yaml`, `evals/<case>/fixture.sh`, `evals/<case>/prompt.md` and `evals/<case>/graders/*.md`.

**Interfaces:**
- Consumes: the hooks from Task 1 (loaded automatically in the with-plugin arm).
- Produces: case names `js-deep-copy`, `py-csv-quoted`, `py-timezone`, `js-currency`, `ts-validate-installed`, `py-retry`, `subagent-semver-installed`, `control-no-new-dep`. Task 4 reads these by name.

Grader conventions, verified with a probe run on 2026-10-14:
- `pattern` goes in YAML single quotes, so backslashes are literal.
- Quote characters inside a pattern are written `[\x22\x27]`.
- A missing target file makes the grader fail, never pass.
- Every `case.yaml` has the same shape: `schema_version: "1.1"`, `name: <case>`, `context.scaffold_script: fixture.sh`.

- [ ] **Step 1: Case `js-deep-copy`**

`evals/js-deep-copy/case.yaml`:

```yaml
schema_version: "1.1"
name: js-deep-copy
context:
  scaffold_script: fixture.sh
```

`evals/js-deep-copy/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "settings-demo",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > settings.js <<'EOF'
export const defaults = {
  theme: { mode: "light", accent: "#3366ff" },
  editor: { tabSize: 2, rulers: [80, 120] },
  updatedAt: new Date("2026-01-01T00:00:00Z"),
};

// Returns the user's settings: the defaults with their overrides applied.
export function userSettings(overrides) {
  const settings = defaults;
  if (overrides.mode) settings.theme.mode = overrides.mode;
  if (overrides.tabSize) settings.editor.tabSize = overrides.tabSize;
  if (overrides.ruler) settings.editor.rulers.push(overrides.ruler);
  return settings;
}
EOF
```

`evals/js-deep-copy/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [stdlib, js]
---

userSettings() in settings.js changes the shared defaults object every time it's called, so one user's overrides leak into the next user's settings. Fix it so each call starts from its own copy of the defaults. Only change settings.js.
```

`evals/js-deep-copy/graders/uses-structured-clone.md`:

```markdown
---
type: regex
pattern: 'structuredClone\('
target:
  source: file
  path: settings.js
---
```

`evals/js-deep-copy/graders/no-json-round-trip.md`:

```markdown
---
type: regex
pattern: 'JSON\.parse\(\s*JSON\.stringify'
match: not_contains
target:
  source: file
  path: settings.js
---
```

- [ ] **Step 2: Case `py-csv-quoted`**

`evals/py-csv-quoted/case.yaml`:

```yaml
schema_version: "1.1"
name: py-csv-quoted
context:
  scaffold_script: fixture.sh
```

`evals/py-csv-quoted/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > orders.csv <<'EOF'
order_id,customer,amount
1001,"Smith, Jane",19.99
1002,Acme Corp,250.00
1003,"Lee, ""Sam""",5.01
EOF
```

`evals/py-csv-quoted/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [stdlib, python]
---

Write total.py: it should print the sum of the amount column in orders.csv.
```

`evals/py-csv-quoted/graders/uses-csv-module.md`:

```markdown
---
type: regex
pattern: 'csv\.(?:reader|DictReader)\(|from\s+csv\s+import'
target:
  source: file
  path: total.py
---
```

`evals/py-csv-quoted/graders/no-naive-split.md`:

```markdown
---
type: regex
pattern: '\.split\(\s*[\x22\x27],[\x22\x27]\s*\)'
match: not_contains
target:
  source: file
  path: total.py
---
```

- [ ] **Step 3: Case `py-timezone`**

`evals/py-timezone/case.yaml`:

```yaml
schema_version: "1.1"
name: py-timezone
context:
  scaffold_script: fixture.sh
```

`evals/py-timezone/fixture.sh`. The dates straddle the 2026 US DST changes, so a fixed offset is wrong for some of them.

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > events.py <<'EOF'
from datetime import datetime, timezone

EVENTS = [
    ("Launch", datetime(2026, 3, 8, 6, 30, tzinfo=timezone.utc)),
    ("Review", datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc)),
    ("Retro", datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc)),
]


def show(events=EVENTS):
    for name, when in events:
        print(f"{name}: {when:%Y-%m-%d %H:%M %Z}")


if __name__ == "__main__":
    show()
EOF
```

`evals/py-timezone/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [stdlib, python]
---

Our users are in New York. Change show() in events.py so it prints each event in New York local time instead of UTC.
```

`evals/py-timezone/graders/uses-zoneinfo.md`:

```markdown
---
type: regex
pattern: 'ZoneInfo\('
target:
  source: file
  path: events.py
---
```

`evals/py-timezone/graders/no-fixed-offset.md`:

```markdown
---
type: regex
pattern: 'hours\s*=\s*-?\s*[45]\b'
match: not_contains
target:
  source: file
  path: events.py
---
```

- [ ] **Step 4: Case `js-currency`**

`evals/js-currency/case.yaml`:

```yaml
schema_version: "1.1"
name: js-currency
context:
  scaffold_script: fixture.sh
```

`evals/js-currency/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "storefront",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > prices.js <<'EOF'
// Formats a price in euros for display on the storefront.
export function formatPrice(amount) {
  return "€" + amount.toFixed(2);
}
EOF
```

`evals/js-currency/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [stdlib, js]
---

formatPrice() in prices.js is used on our German storefront, but 1234.5 comes out as "€1234.50". Make it format euro amounts the way German customers expect.
```

`evals/js-currency/graders/uses-intl.md`:

```markdown
---
type: regex
pattern: 'Intl\.NumberFormat|toLocaleString\(\s*[\x22\x27]de'
target:
  source: file
  path: prices.js
---
```

- [ ] **Step 5: Case `ts-validate-installed`**

`evals/ts-validate-installed/case.yaml`:

```yaml
schema_version: "1.1"
name: ts-validate-installed
context:
  scaffold_script: fixture.sh
```

`evals/ts-validate-installed/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "signup-api",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "typescript": "^5.8.0"
  }
}
EOF
mkdir -p src
cat > src/signup.ts <<'EOF'
export type Signup = { email: string; age: number; referralCode?: string };

// Called with the parsed JSON body of POST /signup.
export function parseSignup(body: unknown): Signup {
  return body as Signup;
}
EOF
```

`evals/ts-validate-installed/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [installed, ts]
---

parseSignup() in src/signup.ts trusts whatever the client sends. Make it validate the body: email must be a valid email address, age a whole number of at least 13, referralCode optional. Throw an error on bad input.
```

`evals/ts-validate-installed/graders/uses-zod.md`:

```markdown
---
type: regex
pattern: 'from\s+[\x22\x27]zod[\x22\x27]|require\(\s*[\x22\x27]zod[\x22\x27]\s*\)'
target:
  source: file
  path: src/signup.ts
---
```

- [ ] **Step 6: Case `py-retry`**

`evals/py-retry/case.yaml`:

```yaml
schema_version: "1.1"
name: py-retry
context:
  scaffold_script: fixture.sh
```

`evals/py-retry/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
requests==2.32.3
EOF
cat > client.py <<'EOF'
import requests

API = "https://api.example.com"


def fetch_user(user_id):
    resp = requests.get(f"{API}/users/{user_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()
EOF
```

`evals/py-retry/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [library, python]
---

fetch_user() in client.py fails now and then with connection errors and 503 responses from the API. Make it retry with exponential backoff before giving up.
```

`evals/py-retry/graders/uses-retry-library.md`. This accepts tenacity, backoff, stamina, or urllib3's `Retry`, which `requests` already installs.

```markdown
---
type: regex
pattern: '(?:import|from)\s+(?:tenacity|backoff|stamina)\b|\bRetry\('
target:
  source: file
  path: client.py
---
```

`evals/py-retry/graders/no-sleep-loop.md`:

```markdown
---
type: regex
pattern: '\bsleep\('
match: not_contains
target:
  source: file
  path: client.py
---
```

- [ ] **Step 7: Case `subagent-semver-installed`**

`evals/subagent-semver-installed/case.yaml`:

```yaml
schema_version: "1.1"
name: subagent-semver-installed
context:
  scaffold_script: fixture.sh
```

`evals/subagent-semver-installed/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "release-notes",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "semver": "^7.7.0"
  }
}
EOF
cat > releases.js <<'EOF'
// Returns the git release tags sorted newest first.
export function sortReleases(tags) {
  return tags;
}
EOF
```

`evals/subagent-semver-installed/prompt.md`:

```markdown
---
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Agent]
tags: [installed, subagent, js]
---

Use a general-purpose subagent to implement sortReleases() in releases.js. It gets git tags like "v1.10.0", "v1.9.2" and "v2.0.0-rc.1" and must return them sorted newest first. Have the subagent make the edit, then tell me what it did.
```

`evals/subagent-semver-installed/graders/uses-semver.md`:

```markdown
---
type: regex
pattern: 'from\s+[\x22\x27]semver(?:/[\w/.-]+)?[\x22\x27]|require\(\s*[\x22\x27]semver(?:/[\w/.-]+)?[\x22\x27]\s*\)'
target:
  source: file
  path: releases.js
---
```

`evals/subagent-semver-installed/graders/delegated.md`:

```markdown
---
type: tool_used
tool: Agent
---
```

- [ ] **Step 8: Case `control-no-new-dep`**

`evals/control-no-new-dep/case.yaml`:

```yaml
schema_version: "1.1"
name: control-no-new-dep
context:
  scaffold_script: fixture.sh
```

`evals/control-no-new-dep/fixture.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "text-utils",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > text.js <<'EOF'
// Capitalizes the first letter of each word: "hello world" -> "Hello World".
export function titleCase(s) {
  return s;
}
EOF
```

`evals/control-no-new-dep/prompt.md`:

```markdown
---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [control, js]
---

Implement titleCase() in text.js.
```

`evals/control-no-new-dep/graders/no-new-dependency.md`:

```markdown
---
type: regex
pattern: '"dependencies"\s*:\s*\{\s*\}'
target:
  source: file
  path: package.json
---
```

`evals/control-no-new-dep/graders/implemented.md`:

```markdown
---
type: regex
pattern: 'toUpperCase\('
target:
  source: file
  path: text.js
---
```

- [ ] **Step 9: Trial run (1 run per case, with-plugin arm only)**

Fixture scripts don't need the executable bit; the probe's non-executable `fixture.sh` ran fine.

```bash
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin \
  --runs 1 --ablation none --model claude-haiku-5-5 --no-publish --max-cost-usd 3
```

Expected:
- All 8 cases load, with no `invalid case` and no `No eval cases found`.
- Each grader line reads `matched`, `pattern absent as expected` or `pattern not found`. Scores may be anything at this stage.

If a grader reads `grader threw … does not exist`, the model wrote to a different path. Re-run that case with `--case <name> --keep-temp`, inspect the workspace, and tighten the prompt to name the file. If `subagent-semver-installed` shows the subagent was denied `Write`/`Edit`, don't work around it in the prompt. Report it to the user, because it means tool grants don't reach subagents in eval runs.

- [ ] **Step 10: Commit**

```bash
git add evals
git commit -F - <<'EOF'
test: add library-first eval suite (8 cases, with vs. without plugin)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 4: Measure on Haiku and Sonnet, record results

**Files:**
- Modify: `README.md` (append to `### What library-first does`)
- Modify, only if the bar is missed: `hooks/library-first.md`

**Interfaces:**
- Consumes: the case names from Task 3, and `aggregate-result.json` fields verified by the probe run: `aggregates.overallScore`, `aggregates.meanDelta`, `cases[].name`, `cases[].aggregates.{score,scoreWithout,delta}`, `costUsd`, `partial`.
- Produces: the measured numbers in the README.

- [ ] **Step 1: Run the full suite on Haiku (background; about 48 runs)**

```bash
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin -j 4 \
  --model claude-haiku-5-5 --output-dir evals/results/claude-haiku-5-5 --no-publish --max-cost-usd 20
```

- [ ] **Step 2: Run the full suite on Sonnet (background; about 48 runs)**

```bash
claude plugin eval . --allow-tools Write Edit --scaffold --trust-plugin -j 4 \
  --model claude-sonnet-5-5 --output-dir evals/results/claude-sonnet-5-5 --no-publish --max-cost-usd 20
```

- [ ] **Step 3: Check both runs against the bar**

```bash
for m in claude-haiku-5-5 claude-sonnet-5-5; do
python3 - "evals/results/$m/aggregate-result.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
a, cases = d["aggregates"], {c["name"]: c["aggregates"] for c in d["cases"]}
without = sum(c["scoreWithout"] for c in cases.values()) / len(cases)
print(f"{sys.argv[1]}: without={without:.2f} with={a['overallScore']:.2f} meanDelta={a['meanDelta']:+.2f} cost=${d['costUsd']:.2f} partial={d['partial']}")
for name, c in cases.items():
    print(f"  {name:28} without={c['scoreWithout']:.2f} with={c['score']:.2f} delta={c['delta']:+.2f}")
met = a["overallScore"] >= 0.8 and a["meanDelta"] > 0 and cases["control-no-new-dep"]["score"] == 1.0
print("  BAR MET" if met else "  BAR MISSED")
EOF
done
```

Expected: `BAR MET` for both models, and `partial=False`.

- [ ] **Step 4: If the bar is missed, diagnose before rewording (at most 2 wording iterations)**

For each failing case, re-run it with `--case <name> --runs 1 --keep-temp`, then read the kept `trace.jsonl` and the workspace file. Classify the failure:
- **(a) The convention is absent from the trace:** this is a hook problem. Go back to the Task 1 smoke test.
- **(b) The model quotes the convention as suspicious or asks about it:** the attribution framing tripped injection defenses. Reword `hooks/library-first.md` toward plainer project facts.
- **(c) The model saw it and still hand-rolled:** make the relevant listed area or the step order more concrete in `hooks/library-first.md`.
- **(d) A grader or prompt mistake:** fix the case, not the convention.
- **(e) `control-no-new-dep` added a dependency:** strengthen the "No new dependency…" line.

After each wording change, run `python3 -m unittest discover -s tests -v` and then the failing model's full suite (Step 1 or 2) again. If the bar is still missed after 2 wording iterations, stop. Report the numbers and traces to the user, with the deferred options from the spec (the write-time check, or a per-prompt reminder).

- [ ] **Step 5: Record the results in the README**

Append this paragraph to `### What library-first does` in `README.md`. Take each value from Step 3's output (`without` and `with`, two decimals), and use today's date.

```markdown
Measured with `claude plugin eval` (8 cases × 3 runs per arm, regex graders, 2026-10-DD): Haiku 5.5 scores W without the plugin and X with it; Sonnet 5.5 scores Y without and Z with. The over-correction control (no new dependency for a one-liner) passes with the plugin on both. Cases and fixtures live in `evals/`.
```

Replace `2026-10-DD`, `W`, `X`, `Y` and `Z` with the measured values before committing.

- [ ] **Step 6: Commit**

```bash
git add README.md hooks/library-first.md
git commit -F - <<'EOF'
docs: record library-first eval results on Haiku 5.5 and Sonnet 5.5

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
