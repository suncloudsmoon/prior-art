#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
click==8.1.8
EOF
cat > client.py <<'EOF'
import json
import urllib.request

API = "https://api.example.com"


def fetch_user(user_id):
    with urllib.request.urlopen(f"{API}/users/{user_id}", timeout=5) as resp:
        return json.load(resp)
EOF
