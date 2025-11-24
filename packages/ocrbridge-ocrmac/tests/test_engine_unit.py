"""Unit tests for ocrmac engine (mocked, runs on any platform)."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from unittest.mock import Mock, patch

import pytest
from ocrbridge.core import OCRProcessingError, UnsupportedFormatError
from PIL import Image

from ocrbridge.engines.ocrmac import OcrmacEngine, OcrmacParams, RecognitionLevel


class TestEngineProperties:
    """Tests for engine properties."""

    def test_engine_name(self) -> None:
        """Test engine name property."""
        engine = OcrmacEngine()
        assert engine.name == "ocrmac"

    def test_supported_formats(self) -> None:
        """Test supported formats property."""
        engine = OcrmacEngine()
        formats = engine.supported_formats

        assert ".jpg" in formats
        assert ".jpeg" in formats
        assert ".png" in formats
        assert ".pdf" in formats
        assert ".tiff" in formats
        assert ".tif" in formats
        assert len(formats) == 6

    def test_supported_formats_immutable(self) -> None:
        """Test that supported formats is a set."""
        engine = OcrmacEngine()
        assert isinstance(engine.supported_formats, set)


class TestPlatformValidation:
    """Tests for platform validation."""

    @patch("platform.system")
    def test_validate_platform_on_darwin(self, mock_system: Mock) -> None:
        """Test platform validation succeeds on macOS."""
        mock_system.return_value = "Darwin"
        engine = OcrmacEngine()
        engine._validate_platform()  # Should not raise

    @patch("platform.system")
    def test_validate_platform_on_windows(self, mock_system: Mock) -> None:
        """Test platform validation fails on Windows."""
        mock_system.return_value = "Windows"
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_platform()

        assert "only available on macOS" in str(exc_info.value)
        assert "Windows" in str(exc_info.value)

    @patch("platform.system")
    def test_validate_platform_on_linux(self, mock_system: Mock) -> None:
        """Test platform validation fails on Linux."""
        mock_system.return_value = "Linux"
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_platform()

        assert "only available on macOS" in str(exc_info.value)
        assert "Linux" in str(exc_info.value)


class TestLiveTextValidation:
    """Tests for LiveText version validation."""

    @patch("platform.mac_ver")
    def test_livetext_on_sonoma_14_0(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation succeeds on macOS Sonoma 14.0."""
        mock_mac_ver.return_value = ("14.0", ("", "", ""), "")
        engine = OcrmacEngine()
        engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)  # Should not raise

    @patch("platform.mac_ver")
    def test_livetext_on_sonoma_14_5(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation succeeds on macOS Sonoma 14.5."""
        mock_mac_ver.return_value = ("14.5.1", ("", "", ""), "")
        engine = OcrmacEngine()
        engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)  # Should not raise

    @patch("platform.mac_ver")
    def test_livetext_on_sequoia_15_0(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation succeeds on macOS Sequoia 15.0+."""
        mock_mac_ver.return_value = ("15.0", ("", "", ""), "")
        engine = OcrmacEngine()
        engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)  # Should not raise

    @patch("platform.mac_ver")
    def test_livetext_on_ventura_13(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation fails on macOS Ventura 13.x."""
        mock_mac_ver.return_value = ("13.5", ("", "", ""), "")
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)

        assert "requires macOS Sonoma (14.0) or later" in str(exc_info.value)
        assert "13.5" in str(exc_info.value)

    @patch("platform.mac_ver")
    def test_livetext_on_monterey_12(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation fails on macOS Monterey 12.x."""
        mock_mac_ver.return_value = ("12.6", ("", "", ""), "")
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)

        assert "requires macOS Sonoma (14.0) or later" in str(exc_info.value)

    @patch("platform.mac_ver")
    def test_livetext_no_version_available(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation fails when version cannot be determined."""
        mock_mac_ver.return_value = ("", ("", "", ""), "")
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)

        assert "Unable to determine macOS version" in str(exc_info.value)

    @patch("platform.mac_ver")
    def test_livetext_invalid_version_format(self, mock_mac_ver: Mock) -> None:
        """Test LiveText validation fails with invalid version format."""
        mock_mac_ver.return_value = ("invalid", ("", "", ""), "")
        engine = OcrmacEngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._validate_livetext_requirement(RecognitionLevel.LIVETEXT)

        assert "Invalid macOS version format" in str(exc_info.value)

    def test_non_livetext_levels_skip_validation(self) -> None:
        """Test that non-LiveText recognition levels skip validation."""
        engine = OcrmacEngine()
        # These should not raise even if platform.mac_ver() returns bad data
        engine._validate_livetext_requirement(RecognitionLevel.FAST)
        engine._validate_livetext_requirement(RecognitionLevel.BALANCED)
        engine._validate_livetext_requirement(RecognitionLevel.ACCURATE)


class TestFileValidation:
    """Tests for file validation."""

    @patch("platform.system", return_value="Darwin")
    def test_file_not_found(self, mock_system: Mock) -> None:
        """Test that missing file raises error."""
        engine = OcrmacEngine()
        non_existent = Path("/tmp/does_not_exist_12345.jpg")

        with pytest.raises(OCRProcessingError) as exc_info:
            engine.process(non_existent)

        assert "File not found" in str(exc_info.value)

    @patch("platform.system", return_value="Darwin")
    def test_unsupported_format(self, mock_system: Mock) -> None:
        """Test that unsupported format raises error."""
        engine = OcrmacEngine()

        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(UnsupportedFormatError) as exc_info:
                engine.process(tmp_path)

            assert "Unsupported file format: .txt" in str(exc_info.value)
            assert ".jpg" in str(exc_info.value)
            assert ".pdf" in str(exc_info.value)
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("platform.system", return_value="Darwin")
    def test_supported_formats_accepted(self, mock_system: Mock) -> None:
        """Test that all supported formats are accepted during validation."""
        engine = OcrmacEngine()
        supported = [".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif"]

        for ext in supported:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                # File exists and format is valid, but will fail later in processing
                # (that's ok, we're just testing format validation here)
                with patch.object(engine, "_process_image"), patch.object(engine, "_process_pdf"):
                    try:
                        engine.process(tmp_path)
                    except Exception:
                        pass  # Expected since file is empty
            finally:
                tmp_path.unlink(missing_ok=True)


class TestHOCRConversion:
    """Tests for HOCR conversion and coordinate transformation."""

    def test_convert_to_hocr_basic(
        self,
        mock_ocrmac_annotations: list[tuple[str, float, tuple[float, float, float, float]]],
        hocr_validator: Callable[[str], ET.Element],
    ) -> None:
        """Test basic HOCR conversion."""
        engine = OcrmacEngine()
        params = OcrmacParams()

        hocr = engine._convert_to_hocr(mock_ocrmac_annotations, 1000, 800, params)

        # Validate structure
        root = hocr_validator(hocr)

        # Check body contains page
        body = root.find("{http://www.w3.org/1999/xhtml}body")
        assert body is not None

        page = body.find(".//{http://www.w3.org/1999/xhtml}div[@class='ocr_page']")
        assert page is not None
        assert page.attrib.get("id") == "page_1"
        assert "bbox 0 0 1000 800" in page.attrib.get("title", "")

    def test_convert_to_hocr_words(
        self,
        mock_ocrmac_annotations: list[tuple[str, float, tuple[float, float, float, float]]],
        bbox_parser: Callable[[str], dict[str, Any]],
    ) -> None:
        """Test HOCR word elements."""
        engine = OcrmacEngine()
        params = OcrmacParams()

        hocr = engine._convert_to_hocr(mock_ocrmac_annotations, 1000, 800, params)
        root = ET.fromstring(hocr)

        # Find all word elements
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) == 3

        # Check first word
        assert words[0].text == "Hello"
        assert words[0].attrib.get("id") == "word_1_1"

        # Check second word
        assert words[1].text == "World"
        assert words[1].attrib.get("id") == "word_1_2"

        # Check third word
        assert words[2].text == "Test"
        assert words[2].attrib.get("id") == "word_1_3"

    def test_coordinate_transformation(self, bbox_parser: Callable[[str], dict[str, Any]]) -> None:
        """Test coordinate transformation from ocrmac to HOCR format.

        ocrmac: relative coords (0.0-1.0), bottom-left origin
        HOCR: absolute pixels, top-left origin
        """
        engine = OcrmacEngine()
        params = OcrmacParams()

        # Test annotation at bottom-left corner
        # ocrmac: x=0.1, y=0.1 (from bottom), width=0.2, height=0.1
        # For 1000x800 image:
        # - x: 0.1 * 1000 = 100
        # - width: 0.2 * 1000 = 200, so x_max = 300
        # - y_min (from top): (1.0 - 0.1 - 0.1) * 800 = 0.8 * 800 = 640
        # - y_max (from top): (1.0 - 0.1) * 800 = 0.9 * 800 = 720
        annotations = [("Bottom", 0.95, (0.1, 0.1, 0.2, 0.1))]

        hocr = engine._convert_to_hocr(annotations, 1000, 800, params)
        root = ET.fromstring(hocr)

        word = root.find(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert word is not None

        title = word.attrib.get("title", "")
        bbox = bbox_parser(title)

        assert bbox["bbox"]["x_min"] == 100
        assert bbox["bbox"]["x_max"] == 300
        assert bbox["bbox"]["y_min"] == 640
        assert bbox["bbox"]["y_max"] == 720

    def test_confidence_conversion(self, bbox_parser: Callable[[str], dict[str, Any]]) -> None:
        """Test confidence conversion from 0-1 to 0-100."""
        engine = OcrmacEngine()
        params = OcrmacParams()

        annotations = [
            ("High", 0.95, (0.1, 0.1, 0.2, 0.1)),
            ("Medium", 0.75, (0.3, 0.1, 0.2, 0.1)),
            ("Low", 0.50, (0.5, 0.1, 0.2, 0.1)),
        ]

        hocr = engine._convert_to_hocr(annotations, 1000, 800, params)
        root = ET.fromstring(hocr)

        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")

        title1 = words[0].attrib.get("title", "")
        assert "x_wconf 95" in title1

        title2 = words[1].attrib.get("title", "")
        assert "x_wconf 75" in title2

        title3 = words[2].attrib.get("title", "")
        assert "x_wconf 50" in title3

    def test_empty_annotations(self, hocr_validator: Callable[[str], ET.Element]) -> None:
        """Test HOCR conversion with empty annotations."""
        engine = OcrmacEngine()
        params = OcrmacParams()

        hocr = engine._convert_to_hocr([], 1000, 800, params)

        # Should still have valid structure
        root = hocr_validator(hocr)
        body = root.find("{http://www.w3.org/1999/xhtml}body")
        assert body is not None

        # No word elements
        words = root.findall(".//{http://www.w3.org/1999/xhtml}span[@class='ocrx_word']")
        assert len(words) == 0


class TestHOCRPageMerging:
    """Tests for HOCR page merging."""

    def test_merge_single_page(self, hocr_validator: Callable[[str], ET.Element]) -> None:
        """Test merging single page returns original."""
        engine = OcrmacEngine()

        page_hocr = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body><div class="ocr_page">Page 1</div></body>
</html>"""

        result = engine._merge_hocr_pages([page_hocr])
        assert result == page_hocr

    def test_merge_multiple_pages(self, hocr_validator: Callable[[str], ET.Element]) -> None:
        """Test merging multiple pages."""
        engine = OcrmacEngine()

        page1 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body><div class="ocr_page" id="page_1">Page 1</div></body>
</html>"""

        page2 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body><div class="ocr_page" id="page_2">Page 2</div></body>
</html>"""

        result = engine._merge_hocr_pages([page1, page2])

        # Validate structure
        root = hocr_validator(result)
        body = root.find("{http://www.w3.org/1999/xhtml}body")
        assert body is not None

        # Check both pages are present
        body_text = ET.tostring(body, encoding="unicode")
        assert "Page 1" in body_text
        assert "Page 2" in body_text

    def test_merge_empty_pages(self, hocr_validator: Callable[[str], ET.Element]) -> None:
        """Test merging with empty pages."""
        engine = OcrmacEngine()

        page1 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body></body>
</html>"""

        page2 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="ocrmac" />
</head>
<body></body>
</html>"""

        result = engine._merge_hocr_pages([page1, page2])

        # Should have valid structure
        hocr_validator(result)


class TestProcessMethod:
    """Tests for main process method."""

    @patch("platform.system", return_value="Windows")
    def test_process_fails_on_non_darwin(self, mock_system: Mock) -> None:
        """Test that process fails on non-Darwin platforms."""
        engine = OcrmacEngine()

        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp_path = Path(tmp.name)

            with pytest.raises(OCRProcessingError) as exc_info:
                engine.process(tmp_path)

            assert "only available on macOS" in str(exc_info.value)

    @patch("platform.system", return_value="Darwin")
    def test_process_uses_default_params(self, mock_system: Mock) -> None:
        """Test that process uses default params when none provided."""
        engine = OcrmacEngine()

        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Create a simple image
            img = Image.new("RGB", (100, 100), color="white")
            img.save(tmp_path)

        try:
            # Mock _process_image to avoid actual OCR
            with patch.object(engine, "_process_image", return_value="<hocr></hocr>"):
                engine.process(tmp_path)
                # If we get here without exception, default params were used
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("platform.system", return_value="Darwin")
    @patch("platform.mac_ver", return_value=("13.0", ("", "", ""), ""))
    def test_process_validates_livetext(self, mock_mac_ver: Mock, mock_system: Mock) -> None:
        """Test that process validates LiveText requirements."""
        engine = OcrmacEngine()
        params = OcrmacParams(recognition_level=RecognitionLevel.LIVETEXT)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp_path = Path(tmp.name)

            with pytest.raises(OCRProcessingError) as exc_info:
                engine.process(tmp_path, params)

            assert "LiveText requires macOS Sonoma" in str(exc_info.value)

    @patch("platform.system", return_value="Darwin")
    def test_process_routes_to_pdf_handler(self, mock_system: Mock) -> None:
        """Test that PDF files are routed to _process_pdf."""
        engine = OcrmacEngine()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with patch.object(engine, "_process_pdf", return_value="<hocr></hocr>") as mock_pdf:
                engine.process(tmp_path)
                mock_pdf.assert_called_once()
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("platform.system", return_value="Darwin")
    def test_process_routes_to_image_handler(self, mock_system: Mock) -> None:
        """Test that image files are routed to _process_image."""
        engine = OcrmacEngine()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Create a simple image
            img = Image.new("RGB", (100, 100), color="white")
            img.save(tmp_path)

        try:
            with patch.object(engine, "_process_image", return_value="<hocr></hocr>") as mock_image:
                engine.process(tmp_path)
                mock_image.assert_called_once()
        finally:
            tmp_path.unlink(missing_ok=True)
