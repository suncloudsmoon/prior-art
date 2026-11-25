---
type: regex
pattern: 'HTMLParser|re\.(?:sub|compile|finditer|findall|search)\('
match: not_contains
target:
  source: file
  path: mirror.py
---
