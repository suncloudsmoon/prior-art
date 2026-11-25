---
type: regex
pattern: '^\s*(?:pillow|imageio|pypng|opencv-python(?:-headless)?|scikit-image|matplotlib|pygame|wand|pyvips)\b'
flags: im
target:
  source: file
  path: requirements.txt
---
