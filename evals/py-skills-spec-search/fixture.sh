#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF2'
pyyaml==6.0.2
EOF2
cat > skills.py <<'EOF2'
from pathlib import Path


def load_skill(folder: Path) -> dict:
    """The skill's name and description, read from `folder/SKILL.md`. Raises ValueError, with the reason, for a skill
    that breaks the Agent Skills specification (https://agentskills.io/specification)."""
    raise NotImplementedError
EOF2
