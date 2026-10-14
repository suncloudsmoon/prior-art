#!/usr/bin/env python3
"""Print the library-first convention as hook context for the event named in argv[1]."""
import json
import sys
from pathlib import Path

convention = (Path(__file__).parent / "library-first.md").read_text(encoding="utf-8")
print(json.dumps({"hookSpecificOutput": {"hookEventName": sys.argv[1], "additionalContext": convention}}))
