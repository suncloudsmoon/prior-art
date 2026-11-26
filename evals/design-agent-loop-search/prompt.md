---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, WebSearch, WebFetch]
tags: [reuse, design, search, field]
---

I'm adding a Chat mode to this app. A local model calls tools in a loop, the way Claude Code does: library search, MCP servers and skills. How should the loop be built? Give me the options and your pick. Don't write code yet.
