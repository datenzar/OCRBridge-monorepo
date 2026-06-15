"""Shared pytest fixtures and utilities for tests."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def samples_dir() -> Path:
    """Return path to samples directory."""
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def sample_jpg(samples_dir: Path) -> Path:
    """Return path to sample JPG file."""
    return samples_dir / "numbers_gs150.jpg"


@pytest.fixture
def sample_jpg_2(samples_dir: Path) -> Path:
    """Return path to second sample JPG file."""
    return samples_dir / "stock_gs200.jpg"


@pytest.fixture
def sample_pdf_en(samples_dir: Path) -> Path:
    """Return path to English contract PDF."""
    return samples_dir / "contract_en_photo.pdf"


@pytest.fixture
def sample_pdf_de(samples_dir: Path) -> Path:
    """Return path to German contract PDF."""
    return samples_dir / "contract_de_scan.pdf"


@pytest.fixture
def mock_ocrmac_annotations() -> list[tuple[str, float, tuple[float, float, float, float]]]:
    """Return mock ocrmac annotation data.

    Format: [(text, confidence, (x_min, y_min, width, height)), ...]
    Coordinates are relative (0.0-1.0) from bottom-left origin.
    """
    return [
        ("Hello", 0.95, (0.1, 0.8, 0.2, 0.1)),  # Top-left area
        ("World", 0.92, (0.4, 0.8, 0.25, 0.1)),  # Top-center area
        ("Test", 0.98, (0.1, 0.5, 0.15, 0.08)),  # Middle-left area
    ]


@pytest.fixture
def mock_ocrmac_module() -> MagicMock:
    """Return a mock ocrmac module."""
    mock_module = MagicMock()

    # Create a mock OCR class
    mock_ocr_class = MagicMock()
    mock_ocr_instance = MagicMock()

    # Configure the OCR class to return the instance when instantiated
    mock_ocr_class.return_value = mock_ocr_instance

    # Set the OCR class on the module
    mock_module.OCR = mock_ocr_class

    # Configure recognize() to return empty list by default
    mock_ocr_instance.recognize.return_value = []

    return mock_module


@pytest.fixture
def hocr_validator() -> Callable[[str], ET.Element]:
    """Return a function to validate and parse HOCR XML."""

    def validate(hocr_xml: str) -> ET.Element:
        """Validate HOCR XML structure and return parsed root element.

        Args:
            hocr_xml: HOCR XML string

        Returns:
            Parsed XML root element

        Raises:
            AssertionError: If validation fails
        """
        # Parse XML
        root = ET.fromstring(hocr_xml)

        # Validate root element
        assert root.tag == "{http://www.w3.org/1999/xhtml}html"
        # Note: ElementTree stores namespace in tag, not as attribute
        # Check that xmlns is in original string
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in hocr_xml

        # Validate structure
        head = root.find("{http://www.w3.org/1999/xhtml}head")
        assert head is not None, "Missing <head> element"

        body = root.find("{http://www.w3.org/1999/xhtml}body")
        assert body is not None, "Missing <body> element"

        # Validate meta tags
        meta_tags = head.findall("{http://www.w3.org/1999/xhtml}meta")
        assert len(meta_tags) >= 2, "Missing meta tags"

        # Find ocr-system meta tag
        ocr_system_meta = None
        for meta in meta_tags:
            if meta.attrib.get("name") == "ocr-system":
                ocr_system_meta = meta
                break

        assert ocr_system_meta is not None, "Missing ocr-system meta tag"
        assert ocr_system_meta.attrib.get("content") == "ocrmac"

        return root

    return validate


@pytest.fixture
def bbox_parser() -> Callable[[str], dict[str, Any]]:
    """Return a function to parse bbox from HOCR title attribute."""

    def parse(title: str) -> dict[str, Any]:
        """Parse bbox and confidence from HOCR title attribute.

        Args:
            title: HOCR title attribute value (e.g., "bbox 0 0 100 200; x_wconf 95")

        Returns:
            Dictionary with bbox coordinates and confidence
        """
        result: dict[str, Any] = {}

        for part in title.split(";"):
            part = part.strip()
            if part.startswith("bbox "):
                coords = part[5:].split()
                result["bbox"] = {
                    "x_min": int(coords[0]),
                    "y_min": int(coords[1]),
                    "x_max": int(coords[2]),
                    "y_max": int(coords[3]),
                }
            elif part.startswith("x_wconf "):
                result["confidence"] = int(part[8:])

        return result

    return parse


@pytest.fixture(scope="session")
def livetext_available() -> bool:
    """Check if LiveText is actually available and working.

    Returns True if LiveText can be safely used, False otherwise.
    """
    try:
        import platform

        from ocrmac.ocrmac import LIVETEXT_AVAILABLE

        # Check if LiveText is reported as available
        if not LIVETEXT_AVAILABLE:
            return False

        # Check for reasonable macOS version (12.x - 16.x range)
        mac_version = platform.mac_ver()[0]
        if mac_version:
            try:
                major_version = int(mac_version.split(".")[0])
                # Version should be in reasonable range (12-16) and >= 14 for LiveText
                if major_version < 14 or major_version > 16:
                    return False
            except (ValueError, IndexError):
                return False

        return True
    except Exception:
        return False


def pytest_configure(config: Any) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires macOS and ocrmac)"
    )
