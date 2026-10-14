---
type: regex
pattern: '(?:import|from)\s+(?:tenacity|backoff|stamina)\b|\bRetry\('
target:
  source: file
  path: client.py
---
