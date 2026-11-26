---
type: regex
pattern: 'iter_lines\(|httpx\.stream\(|urllib\.request'
match: not_contains
target:
  source: file
  path: docs/plans/stream-chat.md
---
