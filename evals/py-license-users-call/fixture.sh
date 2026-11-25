#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
click==8.1.8
EOF
cat > extract.py <<'EOF'
def page_texts(path):
    """The text of each page of the PDF at `path`, in page order."""
    raise NotImplementedError
EOF
