---
type: regex
pattern: 'requests\.|api\.stripe\.com|urllib\.request'
match: not_contains
target:
  source: file
  path: billing.py
---
