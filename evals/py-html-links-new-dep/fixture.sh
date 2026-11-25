#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
requests==2.32.3
EOF
cat > mirror.py <<'EOF'
def absolutize_links(html, base_url):
    """Return `html` with every href and src made absolute against `base_url`."""
    raise NotImplementedError
EOF
