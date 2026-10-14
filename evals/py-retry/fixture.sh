#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
requests==2.32.3
EOF
cat > client.py <<'EOF'
import requests

API = "https://api.example.com"


def fetch_user(user_id):
    resp = requests.get(f"{API}/users/{user_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()
EOF
