---
type: regex
pattern: 'hours\s*=\s*-?\s*[45]\b'
match: not_contains
target:
  source: file
  path: events.py
---
