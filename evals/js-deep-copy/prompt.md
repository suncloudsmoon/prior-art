---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [stdlib, js]
---

userSettings() in settings.js changes the shared defaults object every time it's called, so one user's overrides leak into the next user's settings. Fix it so each call starts from its own copy of the defaults. Only change settings.js.
