#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "release-notes",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "semver": "^7.7.0"
  }
}
EOF
cat > releases.js <<'EOF'
// Returns the git release tags sorted newest first.
export function sortReleases(tags) {
  return tags;
}
EOF
