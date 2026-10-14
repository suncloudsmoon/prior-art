---
type: regex
pattern: 'from\s+[\x22\x27]semver(?:/[\w/.-]+)?[\x22\x27]|require\(\s*[\x22\x27]semver(?:/[\w/.-]+)?[\x22\x27]\s*\)'
target:
  source: file
  path: releases.js
---
