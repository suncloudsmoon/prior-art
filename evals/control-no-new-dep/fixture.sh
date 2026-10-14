#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "text-utils",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > text.js <<'EOF'
// Capitalizes the first letter of each word: "hello world" -> "Hello World".
export function titleCase(s) {
  return s;
}
EOF
