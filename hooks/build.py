#!/usr/bin/env python3
"""Regenerate the hook payloads from library-first.md and stop-check.md. Run after editing either."""
import json
from pathlib import Path

here = Path(__file__).parent
# The hooks only `cat` these files, so the plugin needs no interpreter at runtime.
for source, event, name in (
    ("library-first.md", "SessionStart", "session-start.json"),
    ("library-first.md", "SubagentStart", "subagent-start.json"),
    ("stop-check.md", "Stop", "stop.json"),
    ("stop-check.md", "SubagentStop", "subagent-stop.json"),
):
    text = (here / source).read_text(encoding="utf-8")
    payload = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    (here / name).write_text(json.dumps(payload) + "\n", encoding="ascii")
