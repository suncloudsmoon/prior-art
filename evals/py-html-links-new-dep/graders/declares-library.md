---
type: regex
pattern: '^\s*(?:beautifulsoup4|bs4|lxml|html5lib|selectolax|parsel|pyquery)\b'
flags: im
target:
  source: file
  path: requirements.txt
---
