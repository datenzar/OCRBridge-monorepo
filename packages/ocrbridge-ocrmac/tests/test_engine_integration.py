"""Integration tests for ocrmac engine (requires macOS and ocrmac installed)."""

import platform
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

import pytest

from ocrbridge.engines.ocrmac import OcrmacEngine, OcrmacParams, RecognitionLevel

# Skip all tests in this module if not on macOS
pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin", reason="Integration tests require macOS"
)


@pytest.fixture
def engine() -> OcrmacEngine:
    """Create engine instance."""
    return OcrmacEngine()


@pytest.mark.integration
class TestImageProcessing:
    """Integration tests for image processing."""

    def test_process_jpg_image(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing a real JPG image."""
        result = engine.process(sample_jpg)

        # Validate HOCR structure
        root = hocr_validator(result)

        # Check that we have some OCR results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0, "Expected OCR to find some words"

        # Verify page dimensions are present
        page = root.find(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert page is not None
        assert "bbox" in page.attrib.get("title", "")

    def test_process_second_jpg_image(
        self,
        engine: OcrmacEngine,
        sample_jpg_2: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing a second JPG image."""
        result = engine.process(sample_jpg_2)

        # Validate HOCR structure
        root = hocr_validator(result)

        # Check that we have OCR results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0, "Expected OCR to find some words"

    def test_process_with_fast_recognition(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing with FAST recognition level."""
        params = OcrmacParams(recognition_level=RecognitionLevel.FAST)
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_process_with_balanced_recognition(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing with BALANCED recognition level (default)."""
        params = OcrmacParams(recognition_level=RecognitionLevel.BALANCED)
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_process_with_accurate_recognition(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing with ACCURATE recognition level."""
        params = OcrmacParams(recognition_level=RecognitionLevel.ACCURATE)
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_process_with_livetext_recognition(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
        livetext_available: bool,
    ) -> None:
        """Test processing with LIVETEXT recognition level (Sonoma 14.0+ only)."""
        if not livetext_available:
            pytest.skip("LiveText not available or not working on this system")

        params = OcrmacParams(recognition_level=RecognitionLevel.LIVETEXT)
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_process_with_language_preference(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing with language preference."""
        params = OcrmacParams(languages=["en-US"])
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_process_with_multiple_languages(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing with multiple language preferences."""
        params = OcrmacParams(languages=["en-US", "de-DE", "fr-FR"])
        result = engine.process(sample_jpg, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0


@pytest.mark.integration
class TestPDFProcessing:
    """Integration tests for PDF processing."""

    def test_process_english_pdf(
        self,
        engine: OcrmacEngine,
        sample_pdf_en: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing an English PDF."""
        result = engine.process(sample_pdf_en)

        # Validate HOCR structure
        root = hocr_validator(result)

        # Check that we have OCR results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0, "Expected OCR to find words in PDF"

        # Check for page structure
        pages = root.findall(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert len(pages) > 0, "Expected at least one page"

    def test_process_german_pdf(
        self,
        engine: OcrmacEngine,
        sample_pdf_de: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing a German PDF."""
        params = OcrmacParams(languages=["de-DE"])
        result = engine.process(sample_pdf_de, params)

        # Validate HOCR structure
        root = hocr_validator(result)

        # Check that we have OCR results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0, "Expected OCR to find words in German PDF"

    def test_pdf_multipage_structure(
        self,
        engine: OcrmacEngine,
        sample_pdf_en: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test that multi-page PDFs have correct structure."""
        result = engine.process(sample_pdf_en)

        # Validate HOCR structure
        root = hocr_validator(result)

        # Find all pages
        pages = root.findall(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert len(pages) >= 1, "Expected at least one page"

        # Each page should have bbox in title
        for page in pages:
            title = page.attrib.get("title", "")
            assert "bbox" in title, f"Page missing bbox in title: {title}"

    def test_pdf_with_fast_recognition(
        self,
        engine: OcrmacEngine,
        sample_pdf_en: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test PDF processing with FAST recognition level."""
        params = OcrmacParams(recognition_level=RecognitionLevel.FAST)
        result = engine.process(sample_pdf_en, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_pdf_with_accurate_recognition(
        self,
        engine: OcrmacEngine,
        sample_pdf_en: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test PDF processing with ACCURATE recognition level."""
        params = OcrmacParams(recognition_level=RecognitionLevel.ACCURATE)
        result = engine.process(sample_pdf_en, params)

        # Should return valid HOCR
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0


@pytest.mark.integration
class TestHOCROutput:
    """Integration tests for HOCR output validation."""

    def test_hocr_has_xml_declaration(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that HOCR output has XML declaration."""
        result = engine.process(sample_jpg)
        assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_hocr_has_doctype(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that HOCR output has DOCTYPE."""
        result = engine.process(sample_jpg)
        assert "<!DOCTYPE html" in result
        assert "XHTML 1.0 Transitional" in result

    def test_hocr_has_namespace(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that HOCR output has XHTML namespace."""
        result = engine.process(sample_jpg)
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in result

    def test_hocr_word_bboxes_are_valid(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that all word bboxes are valid (x_min < x_max, y_min < y_max)."""
        result = engine.process(sample_jpg)
        root = ET.fromstring(result)

        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")

        for word in words:
            title = word.attrib.get("title", "")
            # Extract bbox
            bbox_part = [p for p in title.split(";") if p.strip().startswith("bbox")]
            assert len(bbox_part) > 0, f"No bbox found in word title: {title}"

            coords = bbox_part[0].strip()[5:].split()
            x_min, y_min, x_max, y_max = map(int, coords)

            assert x_min < x_max, f"Invalid bbox: x_min ({x_min}) >= x_max ({x_max})"
            assert y_min < y_max, f"Invalid bbox: y_min ({y_min}) >= y_max ({y_max})"
            assert x_min >= 0, f"Invalid bbox: x_min ({x_min}) < 0"
            assert y_min >= 0, f"Invalid bbox: y_min ({y_min}) < 0"

    def test_hocr_confidence_in_range(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that all confidence values are in range 0-100."""
        result = engine.process(sample_jpg)
        root = ET.fromstring(result)

        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")

        for word in words:
            title = word.attrib.get("title", "")
            # Extract confidence
            conf_part = [p for p in title.split(";") if p.strip().startswith("x_wconf")]

            if conf_part:
                conf_str = conf_part[0].strip()[8:]
                confidence = int(conf_str)
                assert 0 <= confidence <= 100, f"Confidence out of range: {confidence}"

    def test_hocr_words_have_text(self, engine: OcrmacEngine, sample_jpg: Path) -> None:
        """Test that all word elements have non-empty text."""
        result = engine.process(sample_jpg)
        root = ET.fromstring(result)

        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")

        for word in words:
            text = word.text
            assert text is not None, "Word element has None text"
            assert len(text.strip()) > 0, "Word element has empty text"

    def test_hocr_page_bbox_matches_image_size(
        self, engine: OcrmacEngine, sample_jpg: Path
    ) -> None:
        """Test that page bbox matches actual image dimensions."""
        from PIL import Image

        # Get actual image dimensions
        with Image.open(sample_jpg) as img:
            img_width, img_height = img.size

        # Process and check HOCR
        result = engine.process(sample_jpg)
        root = ET.fromstring(result)

        page = root.find(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert page is not None

        title = page.attrib.get("title", "")
        bbox_part = [p for p in title.split(";") if p.strip().startswith("bbox")]
        assert len(bbox_part) > 0

        coords = bbox_part[0].strip()[5:].split()
        x_min, y_min, x_max, y_max = map(int, coords)

        assert x_min == 0, "Page bbox x_min should be 0"
        assert y_min == 0, "Page bbox y_min should be 0"
        assert x_max == img_width, f"Page bbox x_max ({x_max}) != image width ({img_width})"
        assert y_max == img_height, f"Page bbox y_max ({y_max}) != image height ({img_height})"


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow_jpg(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test complete workflow from JPG to HOCR."""
        # Process with custom params
        params = OcrmacParams(languages=["en-US"], recognition_level=RecognitionLevel.BALANCED)
        result = engine.process(sample_jpg, params)

        # Validate structure
        root = hocr_validator(result)

        # Verify we got results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

        # Verify XML is well-formed
        assert "<?xml" in result
        assert "</html>" in result

    def test_complete_workflow_pdf(
        self,
        engine: OcrmacEngine,
        sample_pdf_en: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test complete workflow from PDF to HOCR."""
        # Process with custom params
        params = OcrmacParams(languages=["en-US"], recognition_level=RecognitionLevel.FAST)
        result = engine.process(sample_pdf_en, params)

        # Validate structure
        root = hocr_validator(result)

        # Verify we got results
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

        # Verify pages
        pages = root.findall(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert len(pages) >= 1

    def test_default_params_workflow(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test workflow with default parameters."""
        # Process with no params (should use defaults)
        result = engine.process(sample_jpg)

        # Should still work
        root = hocr_validator(result)
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) > 0

    def test_multiple_files_workflow(
        self,
        engine: OcrmacEngine,
        sample_jpg: Path,
        sample_jpg_2: Path,
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test processing multiple files in sequence."""
        # Process first file
        result1 = engine.process(sample_jpg)
        root1 = hocr_validator(result1)
        words1 = root1.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words1) > 0

        # Process second file
        result2 = engine.process(sample_jpg_2)
        root2 = hocr_validator(result2)
        words2 = root2.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words2) > 0

        # Results should be different
        assert result1 != result2
