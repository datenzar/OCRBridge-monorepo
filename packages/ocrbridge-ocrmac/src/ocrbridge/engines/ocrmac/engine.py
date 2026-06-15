"""ocrmac OCR engine implementation - macOS only."""

import importlib
import platform
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence, Tuple

from pdf2image import convert_from_path  # type: ignore[reportUnknownVariableType]
from PIL import Image

from ocrbridge.core import (  # type: ignore[reportMissingTypeStubs]
    OCREngine,
    OCREngineParams,
    OCRProcessingError,
    UnsupportedFormatError,
)

from .models import OcrmacParams, RecognitionLevel  # type: ignore[reportMissingTypeStubs]

Annotation = tuple[str, float, Tuple[float, float, float, float]]
AbsoluteWord = tuple[int, str, int, int, int, int, int]


class OcrmacEngine(OCREngine):
    """ocrmac OCR engine implementation.

    Uses Apple's Vision framework for OCR on macOS.
    Platform: macOS 10.15+ (macOS Sonoma 14.0+ for LiveText)
    """

    __param_model__ = OcrmacParams

    @property
    def name(self) -> str:
        """Return engine name."""
        return "ocrmac"

    @property
    def supported_formats(self) -> set[str]:
        """Return supported file extensions."""
        return {".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif"}

    def _validate_platform(self) -> None:
        """Validate that we're running on macOS."""
        if platform.system() != "Darwin":
            raise OCRProcessingError(
                f"ocrmac is only available on macOS systems. Current platform: {platform.system()}"
            )

    def _validate_livetext_requirement(self, recognition_level: RecognitionLevel) -> None:
        """Validate macOS version for LiveText."""
        if recognition_level != RecognitionLevel.LIVETEXT:
            return

        mac_version = platform.mac_ver()[0]
        if not mac_version:
            raise OCRProcessingError(
                "Unable to determine macOS version. LiveText requires macOS Sonoma (14.0) or later."
            )

        try:
            major_version = int(mac_version.split(".")[0])
            if major_version < 14:
                raise OCRProcessingError(
                    (
                        "LiveText requires macOS Sonoma (14.0) or later. "
                        f"Current version: {mac_version}"
                    )
                )
        except (ValueError, IndexError) as e:
            raise OCRProcessingError(f"Invalid macOS version format: {mac_version}") from e

    def process(self, file_path: Path, params: OCREngineParams | None = None) -> str:
        """Process document using ocrmac and return HOCR XML.

        Args:
            file_path: Path to image or PDF file
            params: ocrmac parameters

        Returns:
            HOCR XML string

        Raises:
            OCRProcessingError: If processing fails or platform requirements not met
            UnsupportedFormatError: If file format not supported
        """
        # Validate platform
        self._validate_platform()

        # Use defaults if no params provided
        if params is None:
            params = OcrmacParams()
        elif not isinstance(params, OcrmacParams):
            params = OcrmacParams.model_validate(params.model_dump())

        # Validate LiveText requirements
        self._validate_livetext_requirement(params.recognition_level)

        # Validate file exists
        if not file_path.exists():
            raise OCRProcessingError(f"File not found: {file_path}")

        # Validate file format
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_formats:
            raise UnsupportedFormatError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {', '.join(sorted(self.supported_formats))}"
            )

        try:
            # Handle PDF separately
            if suffix == ".pdf":
                return self._process_pdf(file_path, params)
            else:
                return self._process_image(file_path, params)

        except Exception as e:
            raise OCRProcessingError(f"ocrmac processing failed: {e}") from e

    def _process_image(self, image_path: Path, params: OcrmacParams) -> str:
        """Process image with ocrmac."""
        try:
            ocrmac = importlib.import_module("ocrmac.ocrmac")
        except ImportError as e:
            raise OCRProcessingError(
                "ocrmac not installed. Install with: pip install ocrmac"
            ) from e

        # Determine framework
        framework_type = (
            "livetext" if params.recognition_level == RecognitionLevel.LIVETEXT else "vision"
        )

        # Create OCR instance
        if params.recognition_level == RecognitionLevel.LIVETEXT:
            ocr_instance = ocrmac.OCR(
                str(image_path),
                language_preference=params.languages,
                framework=framework_type,
            )
        elif params.recognition_level == RecognitionLevel.BALANCED:
            ocr_instance = ocrmac.OCR(
                str(image_path),
                language_preference=params.languages,
            )
        else:
            ocr_instance = ocrmac.OCR(
                str(image_path),
                language_preference=params.languages,
                recognition_level=params.recognition_level.value,
            )

        # Perform OCR
        annotations = ocr_instance.recognize()

        # Get image dimensions
        with Image.open(image_path) as img:
            image_width, image_height = img.size

        # Convert to HOCR
        hocr_content = self._convert_to_hocr(annotations, image_width, image_height, params)

        return hocr_content

    def _process_pdf(self, pdf_path: Path, params: OcrmacParams) -> str:
        """Process PDF by converting to images then OCR."""
        try:
            ocrmac = importlib.import_module("ocrmac.ocrmac")
        except ImportError as e:
            raise OCRProcessingError(
                "ocrmac not installed. Install with: pip install ocrmac"
            ) from e

        # Convert PDF to images
        try:
            images = convert_from_path(str(pdf_path), dpi=300, thread_count=2)
        except Exception as e:
            raise OCRProcessingError(f"PDF conversion failed: {e}")

        # Process each page
        page_hocr_list: list[str] = []
        for image in images:
            # Save temp image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = Path(tmp_file.name)
                image.save(temp_path, format="PNG")

            try:
                # Process page
                framework_type = (
                    "livetext"
                    if params.recognition_level == RecognitionLevel.LIVETEXT
                    else "vision"
                )

                if params.recognition_level == RecognitionLevel.LIVETEXT:
                    ocr_instance = ocrmac.OCR(
                        str(temp_path),
                        language_preference=params.languages,
                        framework=framework_type,
                    )
                elif params.recognition_level == RecognitionLevel.BALANCED:
                    ocr_instance = ocrmac.OCR(
                        str(temp_path),
                        language_preference=params.languages,
                    )
                else:
                    ocr_instance = ocrmac.OCR(
                        str(temp_path),
                        language_preference=params.languages,
                        recognition_level=params.recognition_level.value,
                    )

                annotations = ocr_instance.recognize()
                image_width, image_height = image.size

                page_hocr = self._convert_to_hocr(annotations, image_width, image_height, params)
                page_hocr_list.append(page_hocr)
            finally:
                temp_path.unlink(missing_ok=True)

        # Merge pages
        if len(page_hocr_list) == 1:
            return page_hocr_list[0]
        else:
            return self._merge_hocr_pages(page_hocr_list)

    def _merge_hocr_pages(self, page_hocr_list: list[str]) -> str:
        """Merge multiple HOCR pages."""
        combined_body = ""
        for page_hocr in page_hocr_list:
            start = page_hocr.find("<body>")
            end = page_hocr.find("</body>")
            if start != -1 and end != -1:
                combined_body += page_hocr[start + 6 : end]

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body>{combined_body}</body>
</html>"""

    def _to_absolute_word(
        self,
        idx: int,
        annotation: Annotation,
        image_width: int,
        image_height: int,
    ) -> AbsoluteWord:
        """Convert an OCR annotation to absolute HOCR word data."""
        text, confidence, bbox = annotation

        x_min = int(bbox[0] * image_width)
        x_max = int((bbox[0] + bbox[2]) * image_width)
        y_min = int((1.0 - bbox[1] - bbox[3]) * image_height)
        y_max = int((1.0 - bbox[1]) * image_height)

        return (idx, text, int(confidence * 100), x_min, y_min, x_max, y_max)

    def _group_words_into_lines(self, words: Sequence[AbsoluteWord]) -> list[list[AbsoluteWord]]:
        """Group absolute-position words into visual lines."""
        if not words:
            return []

        sorted_words = sorted(words, key=lambda word: (word[4], word[3]))
        heights = [max(1, word[6] - word[4]) for word in sorted_words]
        average_height = sum(heights) / len(heights)
        y_tolerance = max(5, int(average_height * 0.6))

        lines: list[list[AbsoluteWord]] = []
        current_line: list[AbsoluteWord] = []
        line_center = 0.0

        for word in sorted_words:
            y_center = (word[4] + word[6]) / 2

            if not current_line:
                current_line.append(word)
                line_center = y_center
                continue

            if abs(y_center - line_center) <= y_tolerance:
                current_line.append(word)
                line_center = sum((item[4] + item[6]) / 2 for item in current_line) / len(
                    current_line
                )
                continue

            lines.append(sorted(current_line, key=lambda item: item[3]))
            current_line = [word]
            line_center = y_center

        if current_line:
            lines.append(sorted(current_line, key=lambda item: item[3]))

        return lines

    def _convert_to_hocr(
        self,
        annotations: Sequence[Annotation],
        image_width: int,
        image_height: int,
        params: OcrmacParams,
    ) -> str:
        """Convert ocrmac annotations to HOCR format.

        ocrmac output: [(text, confidence, [x_min, y_min, width, height]), ...]
        where coordinates are relative (0.0-1.0) and from bottom-left origin
        """
        html = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml")

        # Head
        head = ET.SubElement(html, "head")
        ET.SubElement(
            head,
            "meta",
            attrib={"http-equiv": "content-type", "content": "text/html; charset=utf-8"},
        )
        ET.SubElement(head, "meta", attrib={"name": "ocr-system", "content": "ocrmac"})

        # Body
        body = ET.SubElement(html, "body")
        page = ET.SubElement(
            body,
            "div",
            attrib={
                "class": "ocr_page",
                "id": "page_1",
                "title": f"bbox 0 0 {image_width} {image_height}",
            },
        )

        absolute_words = [
            self._to_absolute_word(idx, annotation, image_width, image_height)
            for idx, annotation in enumerate(annotations, start=1)
        ]
        lines = self._group_words_into_lines(absolute_words)

        word_counter = 1
        for line_idx, line_words in enumerate(lines, start=1):
            line_x_min = min(word[3] for word in line_words)
            line_y_min = min(word[4] for word in line_words)
            line_x_max = max(word[5] for word in line_words)
            line_y_max = max(word[6] for word in line_words)

            line_elem = ET.SubElement(
                page,
                "span",
                attrib={
                    "class": "ocr_line",
                    "id": f"line_1_{line_idx}",
                    "title": f"bbox {line_x_min} {line_y_min} {line_x_max} {line_y_max}",
                },
            )

            for _original_idx, text, confidence, x_min, y_min, x_max, y_max in line_words:
                word_elem = ET.SubElement(
                    line_elem,
                    "span",
                    attrib={
                        "class": "ocrx_word",
                        "id": f"word_1_{word_counter}",
                        "title": f"bbox {x_min} {y_min} {x_max} {y_max}; x_wconf {confidence}",
                    },
                )
                word_elem.text = text
                word_counter += 1

        # Generate HOCR XML
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
        html_content = ET.tostring(html, encoding="unicode", method="xml")

        return f"{xml_declaration}\n{doctype}\n{html_content}"
