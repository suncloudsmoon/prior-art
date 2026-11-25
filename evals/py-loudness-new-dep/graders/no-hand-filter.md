---
type: regex
pattern: 'lfilter\(|sosfilt\(|def\s+\w*k_?weight'
flags: i
match: not_contains
target:
  source: file
  path: audio.py
---
