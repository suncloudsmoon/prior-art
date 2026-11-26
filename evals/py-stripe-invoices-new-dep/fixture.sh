#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF2'
requests==2.32.3
EOF2
cat > billing.py <<'EOF2'
import os

STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"]


def open_invoices(customer_id):
    """Return every open invoice of the customer, across all pages."""
    raise NotImplementedError
EOF2
