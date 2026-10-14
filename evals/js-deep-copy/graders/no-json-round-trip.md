---
type: regex
pattern: 'JSON\.parse\(\s*JSON\.stringify'
match: not_contains
target:
  source: file
  path: settings.js
---
