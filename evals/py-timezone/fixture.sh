#!/usr/bin/env bash
set -euo pipefail
cat > events.py <<'EOF'
from datetime import datetime, timezone

EVENTS = [
    ("Launch", datetime(2026, 3, 8, 6, 30, tzinfo=timezone.utc)),
    ("Review", datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc)),
    ("Retro", datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc)),
]


def show(events=EVENTS):
    for name, when in events:
        print(f"{name}: {when:%Y-%m-%d %H:%M %Z}")


if __name__ == "__main__":
    show()
EOF
