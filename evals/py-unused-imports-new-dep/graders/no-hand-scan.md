---
type: regex
pattern: 'ast\.walk\(|ast\.NodeVisitor|isinstance\(\s*\w+\s*,\s*ast\.Import'
match: not_contains
target:
  source: file
  path: tools/unused_imports.py
---
