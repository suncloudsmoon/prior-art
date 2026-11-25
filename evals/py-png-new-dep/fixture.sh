#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
pytest==8.3.4
EOF
cat > shots.py <<'EOF'
def distinct_colors(path):
    """Number of distinct pixel colors in the PNG screenshot at `path`."""
    raise NotImplementedError
EOF
