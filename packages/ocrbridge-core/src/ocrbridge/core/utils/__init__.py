"""Utility modules for OCR Bridge.

Generic HOCR validation and parsing utilities. Engine-specific HOCR conversion
logic belongs in the respective engine packages (e.g., ocrbridge-easyocr).
"""

from . import hocr, pdf

__all__ = ["hocr", "pdf"]
