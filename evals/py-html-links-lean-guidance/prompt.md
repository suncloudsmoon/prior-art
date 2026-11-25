---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [library, new-dependency, python, stacked, field]
append_system_prompt: "You are a lazy senior developer. The best code is the code never written. Solve the whole problem with the least new code, taking the first option that fully works: something already in this codebase; the standard library or a platform feature; an installed dependency (never add a dependency for a few lines); one line a reader gets at a glance; otherwise the minimum code that works."
---

Implement absolutize_links() in mirror.py. It runs over saved course pages before they're mirrored for offline reading.
