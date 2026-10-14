#!/usr/bin/env bash
set -euo pipefail
cat > orders.csv <<'EOF'
order_id,customer,amount
1001,"Smith, Jane",19.99
1002,Acme Corp,250.00
1003,"Lee, ""Sam""",5.01
EOF
