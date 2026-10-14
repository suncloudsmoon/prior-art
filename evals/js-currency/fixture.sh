#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "storefront",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {}
}
EOF
cat > prices.js <<'EOF'
// Formats a price in euros for display on the storefront.
export function formatPrice(amount) {
  return "€" + amount.toFixed(2);
}
EOF
