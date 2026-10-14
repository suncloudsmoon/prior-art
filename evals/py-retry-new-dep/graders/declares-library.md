---
type: regex
pattern: '^\s*(?:tenacity|backoff|stamina|urllib3|requests)\b'
flags: im
target:
  source: file
  path: requirements.txt
---
