---
type: regex
pattern: '\bsleep\('
match: not_contains
target:
  source: file
  path: client.py
---
