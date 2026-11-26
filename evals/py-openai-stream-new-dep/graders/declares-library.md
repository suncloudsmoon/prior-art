---
type: regex
pattern: '^\s*(?:openai|litellm)\b'
flags: im
target:
  source: file
  path: requirements.txt
---
