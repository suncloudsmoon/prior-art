#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "settings-demo",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > settings.js <<'EOF'
export const defaults = {
  theme: { mode: "light", accent: "#3366ff" },
  editor: { tabSize: 2, rulers: [80, 120] },
  updatedAt: new Date("2026-01-01T00:00:00Z"),
};

// Returns the user's settings: the defaults with their overrides applied.
export function userSettings(overrides) {
  const settings = defaults;
  if (overrides.mode) settings.theme.mode = overrides.mode;
  if (overrides.tabSize) settings.editor.tabSize = overrides.tabSize;
  if (overrides.ruler) settings.editor.rulers.push(overrides.ruler);
  return settings;
}
EOF
