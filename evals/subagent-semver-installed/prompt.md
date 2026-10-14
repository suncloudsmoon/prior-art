---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent]
tags: [installed, subagent, js]
---

Use a general-purpose subagent to implement sortReleases() in releases.js. It gets git tags like "v1.10.0", "v1.9.2" and "v2.0.0-rc.1" and must return them sorted newest first. Have the subagent make the edit, then tell me what it did.
