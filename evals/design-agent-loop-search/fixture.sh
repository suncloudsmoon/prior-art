#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF2'
fastapi==0.115.6
httpx==0.28.1
uvicorn==0.32.1
EOF2
cat > app.py <<'EOF2'
from fastapi import FastAPI

app = FastAPI()
MODEL_URL = "http://127.0.0.1:8080/v1"  # llama-server on this machine, OpenAI chat completions format


@app.get("/api/search")
def search(q: str) -> list[dict]:
    """Passages from the user's library that match the query."""
    return []
EOF2
