---
type: regex
pattern: '(?:import|from)\s+(?:openai|litellm)\b'
target:
  source: file
  path: model_client.py
---
