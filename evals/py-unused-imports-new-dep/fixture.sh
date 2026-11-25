#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
click==8.1.8
EOF
mkdir -p src tools
cat > src/report.py <<'EOF'
import json
import os
import sys


def render(rows):
    return json.dumps(rows, indent=2)
EOF
cat > tools/unused_imports.py <<'EOF'
def unused_imports(root):
    """(file, line, name) for every unused import in the Python files under `root`."""
    raise NotImplementedError
EOF
