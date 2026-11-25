---
type: regex
pattern: '(?:import|from)\s+(?:PIL|imageio|png|cv2|skimage|matplotlib|pygame|wand|pyvips)\b'
target:
  source: file
  path: shots.py
---
