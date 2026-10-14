---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
tags: [library, python]
---

fetch_user() in client.py fails now and then with connection errors and 503 responses from the API. Make it retry with exponential backoff before giving up.
