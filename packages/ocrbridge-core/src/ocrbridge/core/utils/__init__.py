"""Utility modules for OCR Bridge.

Generic HOCR validation and parsing utilities. Engine-specific HOCR conversion
logic belongs in the respective engine packages (e.g., ocrbridge-easyocr).
"""

from .hocr import (
    HOCRInfo,
    HOCRParseError,
    HOCRValidationError,
    extract_bbox,
    parse_hocr,
    validate_hocr,
)

__all__ = [
    "HOCRInfo",
    "HOCRParseError",
    "HOCRValidationError",
    "parse_hocr",
    "validate_hocr",
    "extract_bbox",
]
