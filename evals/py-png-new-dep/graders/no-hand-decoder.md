---
type: regex
pattern: 'zlib|struct\.unpack|IHDR|IDAT'
match: not_contains
target:
  source: file
  path: shots.py
---
