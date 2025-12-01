"""HOCR conversion utilities for EasyOCR engine.

This module handles the conversion of EasyOCR's native output format
(list of bbox, text, confidence tuples) to the standard HOCR XML format.
"""

from typing import Sequence, TypedDict

Point2D = tuple[float, float]
BBox = tuple[int, int, int, int]


class WordData(TypedDict):
    """Word data with bounding box and metadata."""

    text: str
    confidence: float
    bbox: BBox
    y_center: float
    height: float
    x_min: int


class LineData(TypedDict):
    """Line data containing grouped words."""

    bbox: BBox
    words: list[WordData]


EasyOCRResult = tuple[Sequence[Point2D], str, float]


def _group_words_into_lines(easyocr_results: Sequence[EasyOCRResult]) -> list[LineData]:
    """Group EasyOCR word detections into lines based on vertical position.

    Args:
        easyocr_results: List of (bbox, text, confidence) tuples from EasyOCR

    Returns:
        List of line dictionaries, each containing:
            - bbox: (x_min, y_min, x_max, y_max) in pixels
            - words: List of word dictionaries with text, confidence, bbox
    """
    if not easyocr_results:
        return []

    # Convert EasyOCR results to word dictionaries
    words: list[WordData] = []
    for result in easyocr_results:
        # EasyOCR bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        bbox, text, confidence = result

        # Extract coordinates (convert to min/max format)
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))

        # Calculate vertical center for line grouping
        y_center = (y_min + y_max) / 2
        height = y_max - y_min

        words.append(
            {
                "text": text,
                "confidence": confidence,
                "bbox": (x_min, y_min, x_max, y_max),
                "y_center": y_center,
                "height": height,
                "x_min": x_min,
            }
        )

    if not words:
        return []

    # Calculate median word height for threshold
    heights: list[float] = [w["height"] for w in words]
    heights.sort()
    median_height = heights[len(heights) // 2]

    # Threshold: words are on same line if y_centers within 50% of median height
    line_threshold = median_height * 0.5

    # Sort words by vertical position (top to bottom)
    words.sort(key=lambda w: w["y_center"])

    # Group words into lines
    lines: list[list[WordData]] = []
    current_line_words = [words[0]]
    current_y_center = words[0]["y_center"]

    for word in words[1:]:
        # Check if word belongs to current line
        if abs(word["y_center"] - current_y_center) <= line_threshold:
            current_line_words.append(word)
        else:
            # Start new line
            lines.append(current_line_words)
            current_line_words = [word]
            current_y_center = word["y_center"]

    # Don't forget the last line
    if current_line_words:
        lines.append(current_line_words)

    # Process each line: sort words left-to-right and calculate bbox
    result_lines: list[LineData] = []
    for line_words in lines:
        # Sort words left to right
        line_words.sort(key=lambda w: w["x_min"])

        # Calculate line bounding box
        line_x_min = min(w["bbox"][0] for w in line_words)
        line_y_min = min(w["bbox"][1] for w in line_words)
        line_x_max = max(w["bbox"][2] for w in line_words)
        line_y_max = max(w["bbox"][3] for w in line_words)

        result_lines.append(
            {"bbox": (line_x_min, line_y_min, line_x_max, line_y_max), "words": line_words}
        )

    return result_lines


def to_hocr(easyocr_results: Sequence[EasyOCRResult], image_width: int, image_height: int) -> str:
    """Convert EasyOCR results to HOCR XML format with hierarchical structure.

    EasyOCR output format: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], text, confidence), ...]
    HOCR format: XML with bbox coordinates and confidence (x_wconf)
    Creates proper hOCR structure: ocr_page → ocr_line → ocrx_word

    Args:
        easyocr_results: List of (bbox, text, confidence) tuples from EasyOCR
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        HOCR XML string with recognized text and bounding boxes in hierarchical structure
    """
    # Build HOCR XML structure
    hocr_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">',
        "<head>",
        ' <meta http-equiv="content-type" content="text/html; charset=utf-8" />',
        ' <meta name="ocr-system" content="easyocr" />',
        ' <meta name="ocr-capabilities" content="ocr_page ocr_carea ocr_par ocr_line ocrx_word" />',
        "</head>",
        "<body>",
        f'  <div class="ocr_page" id="page_1" title="bbox 0 0 {image_width} {image_height}">',
    ]

    # Group words into lines
    lines = _group_words_into_lines(easyocr_results)

    # Add each line with its words
    word_counter = 1
    for line_idx, line_data in enumerate(lines, start=1):
        line_bbox = line_data["bbox"]

        # Create line element
        hocr_lines.append(
            f'    <span class="ocr_line" id="line_1_{line_idx}" '
            f'title="bbox {line_bbox[0]} {line_bbox[1]} {line_bbox[2]} {line_bbox[3]}">'
        )

        # Add words to this line
        for word_data in line_data["words"]:
            # Convert confidence (0.0-1.0) to percentage (0-100)
            conf_percent = int(word_data["confidence"] * 100)

            # Escape text for XML
            escaped_text = (
                word_data["text"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
            )

            # Create HOCR word element
            word_bbox = word_data["bbox"]
            hocr_lines.append(
                f'      <span class="ocrx_word" id="word_1_{word_counter}" '
                f'title="bbox {word_bbox[0]} {word_bbox[1]} {word_bbox[2]} '
                f'{word_bbox[3]}; x_wconf {conf_percent}">'
                f"{escaped_text}</span>"
            )

            word_counter += 1

        # Close line element
        hocr_lines.append("    </span>")

    # Close HOCR structure
    hocr_lines.extend(["  </div>", "</body>", "</html>"])

    return "\n".join(hocr_lines)
