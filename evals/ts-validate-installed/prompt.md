---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [installed, ts]
---

parseSignup() in src/signup.ts trusts whatever the client sends. Make it validate the body: email must be a valid email address, age a whole number of at least 13, referralCode optional. Throw an error on bad input.
