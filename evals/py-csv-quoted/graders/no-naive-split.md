---
type: regex
pattern: '\.split\(\s*[\x22\x27],[\x22\x27]\s*\)'
match: not_contains
target:
  source: file
  path: total.py
---
