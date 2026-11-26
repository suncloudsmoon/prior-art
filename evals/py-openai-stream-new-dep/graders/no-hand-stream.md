---
type: regex
pattern: 'iter_lines\(|httpx\.|urllib\.request|removeprefix\(|startswith\(.data:'
match: not_contains
target:
  source: file
  path: model_client.py
---
