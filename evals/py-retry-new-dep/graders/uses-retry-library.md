---
type: regex
pattern: '(?:import|from)\s+(?:tenacity|backoff|stamina|urllib3)\b|\bRetry\('
target:
  source: file
  path: client.py
---
