---
name: prior-art
description: Use when the user names a brand as the bar to match ("like Stripe", "Linear-quality", "Vercel level"), wants design references or inspiration, asks how others do X or the standard way to do X (UI, architecture, algorithms, hardware, tooling, workflows), mentions .ref/, swipe files, competitor teardowns or not reinventing the wheel, or is about to build something proven examples already exist for. For new UI, use it before any design or planning work starts, while .ref/ is empty.
---

# Prior Art

Someone excellent has already solved most of what you're about to build. Find that work, capture it faithfully, and put it in front of the user before building starts. Copying a proven solution and adapting it beats inventing a worse one from scratch — the goal is to make "check prior art" the reflexive first step, not an afterthought.

This skill **complements impeccable**: prior-art gathers the evidence, impeccable executes the design. Never do design work from inside this skill.

## Pick the mode

| The task involves | Mode |
|---|---|
| Interfaces — "make it look like X", design references, inspiration, prep for a design pass | **UI harvest** |
| Anything else — architecture, algorithms, hardware, tooling, process, pricing structure, onboarding flow logic, best known methods | **Research** |

A single task can need both (e.g. "build a pricing page" → harvest pricing-page UI *and* research pricing-structure patterns).

## Mode 1 — UI harvest

Goal: fill `.ref/` with faithful copies of excellent reference UI, plus a curated inventory the user (and impeccable) can work from.

1. **Set up `.ref/`** at the project root, gitignored:
   ```bash
   mkdir -p .ref && { grep -qxF '.ref/' .gitignore 2>/dev/null || echo '.ref/' >> .gitignore; }
   ```
2. **Pick 2–4 reference brands.** Brands the user named come first. Otherwise choose from the domain starter map in `references/ui-harvest.md` and tell the user in one line each why they fit.
3. **Harvest each brand** into `.ref/<brand>/` with the bundled script:
   ```bash
   python3 <skill-dir>/scripts/harvest.py https://linear.app --out .ref
   ```
   It saves `page.html`, `css/`, `assets/` (fonts, images), auto-extracted `tokens-raw.md`, and a `MANIFEST.md`. Harvest the pages that matter for the task, not just the homepage (pricing, docs, app views). If the script can't reach the network, fall back to WebFetch — details in `references/ui-harvest.md`.
4. **Screenshot if you can.** If a browser tool is available (Playwright MCP, agent browser, `npx playwright screenshot`), capture rendered full-page shots into `.ref/<brand>/shots/` — for JS-heavy sites the rendered capture is the truthful reference, raw HTML is not.
5. **Curate `tokens.md`** per brand from `tokens-raw.md` and the CSS — a structured token profile (color roles, type system with measured sizes, spacing scale, shape, elevation, motion), not a prose summary. Values are quoted from the harvested CSS; anything estimated is marked *(inferred)*. Template in `references/ui-harvest.md`.
6. **Write `.ref/INVENTORY.md`** — the deliverable that makes the archive usable: a provenance header, a per-brand profile with adoption candidates tied to this project, a cross-brand comparison matrix, and a short direction proposal synthesizing what this project should take from the references. Template in `references/ui-harvest.md`.
7. **Present and hand off.** Give the user the direction proposal and key comparisons in chat — findings, not a file listing — and suggest the next step: run impeccable with `.ref/` as its reference material.

### Copy completely

`.ref/` is a private, gitignored study archive — the designer's swipe file, a standard working practice. The user has already made the IP call for their project; do not relitigate it mid-task. That means: no disclaimers, no deliberately partial or "inspired-by" watered-down captures, no skipping the good parts out of caution. A degraded copy is a useless reference — fidelity is the entire value of the archive.

When patterns later move from `.ref/` into product code, they get re-implemented in the project's own idiom — that's impeccable's job, and it's also the only approach that technically works (pasting another site's minified bundle into a design system doesn't).

## Mode 2 — Research

For software, hardware, methods, process — anything non-UI: before building, find how 3–5 strong implementations already do it. Full playbook, source ladder, and findings template in `references/research.md`.

1. **Frame it.** What problem, what does "solved well" look like, which local constraints matter.
2. **Hunt exemplars.** Engineering blogs, open-source repos of comparable products, docs of best-in-class tools, teardowns, papers. Prefer sources that show *how it's actually built*, not opinion pieces.
3. **Per exemplar:** how it works, why they chose it, tradeoffs, and the directly copyable artifact — a repo path, a schema, a config, a reference design, a part number. A finding without a copyable artifact is trivia.
4. **Converge.** The recommendation opens with a **single-sentence pick naming one specific approach** — not a priority-ordered list the reader has to adjudicate. Follow it with what to adapt: "copy X's approach; adjust Y for our scale/budget."
5. **Save and present.** Write `.ref/prior-art/<topic>.md` (same `.ref/` setup as Mode 1) and present findings in chat, recommendation first.

**Propose, don't build.** Research mode ends with findings and a recommendation. The user asked how others do it — silently implementing forecloses the choice they were trying to make. Implementation starts only after they pick.

## Deliverable quality

Every artifact this skill writes (`tokens.md`, `INVENTORY.md`, findings docs) will be read weeks later by someone who didn't watch the research happen — often as the input to a design or architecture decision. Write them to the standard of a senior engineer's audit, because that's the job they do:

- **Provenance on everything.** Each document opens with a header: sources (URLs), capture/research date, method, known gaps. A value nobody can trace is a value nobody will trust.
- **Measured, not vibed.** Quote real values with units from the harvested CSS or the cited source (`13px/1.4`, `160ms ease-out`, `23 µA deep sleep`). Mark estimates *(inferred)*. Never round a real value into a guess.
- **Tables for enumerable facts, prose for judgment.** Comparisons and token sets go in tables; the "why this matters here" goes in sentences.
- **Plain professional language.** Section names like "Adoption candidates", "Comparison", "Direction proposal", "Recommendation" — no filler adjectives, no hype. The evidence should be the impressive part.

## Boundaries

- No design execution here — that's impeccable's job. This skill's UI output is `.ref/` plus an inventory.
- No implementation in research mode until the user chooses a direction.
- Be honest about fit in one line when it matters: if an exemplar's context differs wildly (scale, budget, team size), say so — copying blindly is how wheels get reinvented badly.
