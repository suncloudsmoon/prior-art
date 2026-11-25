---
type: regex
pattern: '(?:import|from)\s+(?:vendor\.)?fastpdf\b|from\s+vendor\s+import\s+fastpdf'
target:
  source: file
  path: extract.py
---
