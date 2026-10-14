#!/usr/bin/env python3
"""Regenerate the hook payloads from library-first.md. Run after editing the convention."""
import json
from pathlib import Path

here = Path(__file__).parent
convention = (here / "library-first.md").read_text(encoding="utf-8")
# The hooks only `cat` these files, so the plugin needs no interpreter at runtime.
for event, name in (("SessionStart", "session-start.json"), ("SubagentStart", "subagent-start.json")):
    payload = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": convention}}
    (here / name).write_text(json.dumps(payload) + "\n", encoding="ascii")
