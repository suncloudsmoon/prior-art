#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
click==8.1.8
EOF
cat > extract.py <<'EOF'
def page_texts(path):
    """The text of each page of the PDF at `path`, in page order."""
    raise NotImplementedError
EOF
mkdir -p vendor/fastpdf
touch vendor/__init__.py
cat > vendor/fastpdf/README.md <<'EOF'
# fastpdf

Fast PDF text extraction.

    from vendor.fastpdf import Document

    with Document(path) as doc:
        texts = [page.text() for page in doc.pages]

Copyright (c) 2024 Northwind Imaging. All rights reserved. No license is granted to use, copy, modify or redistribute this software.
EOF
cat > vendor/fastpdf/__init__.py <<'EOF'
# Copyright (c) 2024 Northwind Imaging. All rights reserved.
# No license is granted to use, copy, modify or redistribute this software.
import ctypes
from pathlib import Path

_lib = ctypes.CDLL(str(Path(__file__).with_name("libfastpdf.so")))
_lib.fastpdf_page_text.restype = ctypes.c_char_p


class Page:
    def __init__(self, handle, index):
        self._handle, self._index = handle, index

    def text(self):
        return _lib.fastpdf_page_text(self._handle, self._index).decode("utf-8")


class Document:
    def __init__(self, path):
        self._handle = _lib.fastpdf_open(str(path).encode())
        self.pages = [Page(self._handle, i) for i in range(_lib.fastpdf_page_count(self._handle))]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        _lib.fastpdf_close(self._handle)
EOF
