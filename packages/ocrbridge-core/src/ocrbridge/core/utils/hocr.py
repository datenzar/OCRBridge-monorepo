"""HOCR XML parsing and validation utilities.

This module provides generic utilities for validating and parsing HOCR XML output.
Engine-specific HOCR conversion logic belongs in the respective engine packages.
"""

import re
import xml.etree.ElementTree as ET
from typing import NamedTuple


class HOCRParseError(Exception):
    """Raised when HOCR parsing fails."""

    pass


class HOCRValidationError(Exception):
    """Raised when HOCR validation fails."""

    pass


class HOCRInfo(NamedTuple):
    """Parsed HOCR information."""

    page_count: int
    word_count: int
    has_bounding_boxes: bool


def parse_hocr(hocr_content: str) -> HOCRInfo:
    """
    Parse HOCR content and extract information.

    Args:
        hocr_content: HOCR XML string

    Returns:
        HOCRInfo with parsed data

    Raises:
        HOCRParseError: If parsing fails
    """
    try:
        root = ET.fromstring(hocr_content)
    except ET.ParseError as e:
        raise HOCRParseError(f"Failed to parse HOCR XML: {e}")

    # Define namespace for XML queries (used if elements not found without it)
    namespace = {"html": "http://www.w3.org/1999/xhtml"}

    # Count pages (elements with class="ocr_page")
    page_count = len(root.findall(".//*[@class='ocr_page']"))
    if page_count == 0:
        # Try with namespace
        page_count = len(root.findall(".//*[@class='ocr_page']", namespace))

    # Count words (elements with class="ocrx_word")
    word_count = len(root.findall(".//*[@class='ocrx_word']"))
    if word_count == 0:
        # Try with namespace
        word_count = len(root.findall(".//*[@class='ocrx_word']", namespace))

    # Check for bounding boxes
    has_bounding_boxes = "bbox" in hocr_content

    return HOCRInfo(
        page_count=page_count,
        word_count=word_count,
        has_bounding_boxes=has_bounding_boxes,
    )


def validate_hocr(hocr_content: str) -> None:
    """
    Validate HOCR content meets requirements.

    Args:
        hocr_content: HOCR XML string

    Raises:
        HOCRValidationError: If validation fails
    """
    try:
        info = parse_hocr(hocr_content)
    except HOCRParseError as e:
        raise HOCRValidationError(f"HOCR parsing failed: {e}")

    if info.page_count == 0:
        raise HOCRValidationError("HOCR must contain at least one ocr_page")

    if not info.has_bounding_boxes:
        raise HOCRValidationError("HOCR must contain bounding box coordinates")


def extract_bbox(element_title: str) -> tuple[int, int, int, int] | None:
    """Extract bounding box coordinates from title attribute.

    Args:
        element_title: Title attribute value (e.g., "bbox 10 20 50 40")

    Returns:
        Tuple of (x0, y0, x1, y1) or None if no bbox found
    """
    match = re.search(r"bbox (\d+) (\d+) (\d+) (\d+)", element_title)
    if match:
        coords = match.groups()
        return (int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]))
    return None


def merge_hocr_pages(page_hocr_list: list[str], system_name: str = "unknown") -> str:
    """Merge multiple HOCR pages into a single document.

    Args:
        page_hocr_list: List of HOCR XML strings, one per page.
        system_name: Name of the OCR system (e.g., 'tesseract', 'easyocr') to put in metadata.

    Returns:
        Combined HOCR XML string.
    """
    combined_body = ""
    for page_hocr in page_hocr_list:
        # Extract content between <body> tags
        start = page_hocr.find("<body>")
        end = page_hocr.find("</body>")
        if start != -1 and end != -1:
            combined_body += page_hocr[start + 6 : end]

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="{system_name}" />
</head>
<body>{combined_body}</body>
</html>"""
