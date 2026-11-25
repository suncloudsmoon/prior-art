---
type: regex
pattern: '(?:import|from)\s+(?:fitz|pymupdf|pypdf|PyPDF2|pdfplumber|pdfminer|pypdfium2|pdftotext|borb)\b'
target:
  source: file
  path: extract.py
---
