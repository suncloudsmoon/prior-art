#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF2'
fastapi==0.115.6
httpx==0.28.1
EOF2
cat > model_client.py <<'EOF2'
BASE_URL = "http://127.0.0.1:8080/v1"  # llama-server on this machine


def stream_chat(messages, tools):
    """Yield the model's reply as it arrives: ("thinking", text) for each piece of `reasoning_content`,
    ("text", text) for each piece of the answer, then ("tool_call", name, arguments) for each complete tool call."""
    raise NotImplementedError
EOF2
