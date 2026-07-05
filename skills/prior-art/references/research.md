# Prior-Art Research Playbook

For everything that isn't UI harvesting: software design, algorithms, hardware, tooling, workflows, pricing structure, ops practice — any "what's the best known method" question. The output is a findings document and a recommendation, not an implementation.

## Contents
- [Frame the question](#frame-the-question)
- [Source ladder](#source-ladder)
- [What counts as a finding](#what-counts-as-a-finding)
- [Findings document template](#findings-document-template)
- [Presenting](#presenting)

## Frame the question

Before searching, write one sentence each:

1. **Problem**: what actually has to work (not the feature name — the underlying job).
2. **Solved-well looks like**: the observable properties a good solution has.
3. **Local constraints**: scale, budget, team size, stack, power budget, timeline — whatever will filter exemplars later.

This framing decides search terms and, later, the fit-check.

## Source ladder

Work down the ladder; higher rungs show *how it's actually built*, lower rungs are context.

1. **Engineering blogs of companies that run it in production** — Stripe, Cloudflare, Shopify, Figma, Netflix, Uber, Discord, fly.io, etc. These are teardown-grade: architecture diagrams, real numbers, failure stories.
2. **Open-source repos of comparable products** — the strongest form of prior art because the artifact itself is copyable. Read the actual code/config/schema, not the README claims. (Software: GitHub search by topic; infra: their terraform/helm charts; hardware: open designs on GitHub/Hackaday, teardowns on iFixit/EEVblog.)
3. **Docs of best-in-class tools in the space** — how a category leader models the problem (their API shape, their config surface) is distilled prior art.
4. **Postmortems and war stories** — HN/Lobsters threads, conference talks. Best for learning which popular approach quietly fails.
5. **Papers / standards / RFCs** — when the domain has them, they name the canonical algorithms and their tradeoffs.

3–5 exemplars is the target. Fewer means the recommendation rests on anecdote; many more means the doc becomes a survey nobody reads.

## What counts as a finding

Per exemplar, capture four things:

- **How it works** — mechanism, not marketing. Two to five sentences or a small diagram.
- **Why they chose it** — the constraint that drove the choice, when discoverable.
- **Tradeoffs** — what it costs (complexity, money, latency, power, ops burden).
- **Copyable artifact** — the concrete thing to copy: repo path + file, schema, config block, chip part number, BOM line, checklist. **A finding without a copyable artifact is trivia** — keep hunting until there's something to point at.
- **Source, dated and graded** — cite where each claim comes from and tag it *primary* (their code, their docs, their engineering blog) or *secondary* (someone else's writeup). A recommendation built on secondary sources says so.

Save supporting material (schemas, configs, key blog excerpts) into `.ref/prior-art/<topic>/` next to the findings doc when it's worth keeping locally.

## Findings document template

Save as `.ref/prior-art/<topic>.md` (ensure `.ref/` exists and is gitignored — same setup as UI mode):

```markdown
# Prior art: <topic>

| | |
|---|---|
| Date | <date> |
| Problem | <one line — the job that has to work> |
| Constraints | <one line — scale, stack, budget, power, timeline> |
| Sources | <n> primary, <n> secondary (cited inline) |

## Recommendation
**<One sentence naming the single pick: "Adopt X's approach using Y.">**

<2-4 sentences: what that means concretely, and what to adapt for our constraints.>
First step if adopted: <one concrete action>.

## Exemplars

### 1. <Name> — <one-line what it is>
- How: ...
- Why they chose it: ...
- Tradeoffs: ...
- Copyable artifact: <link/path/part number>
- Source: <url> (<date>, primary|secondary)

### 2. ...

## Convergence
| Aspect | <Ex.1> | <Ex.2> | <Ex.3> | Consensus? |
|---|---|---|---|---|

Where the exemplars agree, that's the industry's settled answer — deviating needs a reason.

## Fit check
One or two lines on where our context differs from the exemplars' (scale, budget, team) and what that changes.
```

Recommendation sits at the top on purpose, and its first line is a **single-sentence pick in bold** — a reader who stops after five lines still gets one actionable answer, not a list to adjudicate.

## Presenting

In chat: recommendation first, then one line per exemplar, then the fit check. Link the findings doc for depth. Then **stop — propose, don't build.** Offer the obvious next step ("want me to implement the Stripe-style variant?") and wait for the user to choose. If the user already explicitly asked for implementation in the same breath, confirm the recommendation matches what they meant, then proceed under the normal workflow (not this skill).
