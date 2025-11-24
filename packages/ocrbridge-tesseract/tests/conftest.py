"""Shared pytest fixtures for ocrbridge-tesseract tests."""

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_images():
    """Return paths to sample image files."""
    base_path = Path(__file__).parent.parent / "samples"
    return {
        "numbers": base_path / "numbers_gs150.jpg",
        "stock": base_path / "stock_gs200.jpg",
    }


@pytest.fixture
def sample_pdfs():
    """Return paths to sample PDF files."""
    base_path = Path(__file__).parent.parent / "samples"
    return {
        "contract_en_scan": base_path / "contract_en_scan.pdf",
        "contract_en_photo": base_path / "contract_en_photo.pdf",
        "contract_de_scan": base_path / "contract_de_scan.pdf",
        "contract_de_photo": base_path / "contract_de_photo.pdf",
    }


@pytest.fixture
def mock_hocr_output():
    """Return sample HOCR output for mocking."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="tesseract 5.0.0" />
</head>
<body>
<div class="ocr_page" id="page_1" title="bbox 0 0 100 100">
  <span class="ocrx_word" id="word_1" title="bbox 10 20 40 30">Test</span>
</div>
</body>
</html>"""


@pytest.fixture
def mock_hocr_page():
    """Return sample HOCR page for merging tests."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="ocr-system" content="tesseract 5.0.0" />
</head>
<body>
<div class="ocr_page" id="page_{}" title="bbox 0 0 100 100">
  <span class="ocrx_word" id="word_1" title="bbox 10 20 40 30">Page {}</span>
</div>
</body>
</html>"""


@pytest.fixture
def tesseract_engine():
    """Return TesseractEngine instance."""
    from ocrbridge.engines.tesseract import TesseractEngine

    return TesseractEngine()


@pytest.fixture
def mock_tesseract_success(monkeypatch, mock_hocr_output):
    """Mock successful pytesseract call."""

    def mock_image_to_pdf_or_hocr(*args, **kwargs):
        return mock_hocr_output.encode("utf-8")

    monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_image_to_pdf_or_hocr)


@pytest.fixture
def mock_pdf_convert_success(monkeypatch):
    """Mock successful PDF to image conversion."""
    # Create a simple white image
    fake_image = Image.new("RGB", (100, 100), color="white")

    def mock_convert_from_path(*args, **kwargs):
        return [fake_image]

    monkeypatch.setattr(
        "ocrbridge.engines.tesseract.engine.convert_from_path", mock_convert_from_path
    )


@pytest.fixture
def mock_pdf_convert_multipage(monkeypatch):
    """Mock PDF to image conversion returning multiple pages."""
    fake_image1 = Image.new("RGB", (100, 100), color="white")
    fake_image2 = Image.new("RGB", (100, 100), color="gray")
    fake_image3 = Image.new("RGB", (100, 100), color="lightblue")

    def mock_convert_from_path(*args, **kwargs):
        return [fake_image1, fake_image2, fake_image3]

    monkeypatch.setattr(
        "ocrbridge.engines.tesseract.engine.convert_from_path", mock_convert_from_path
    )


@pytest.fixture
def mock_installed_languages(monkeypatch):
    """Mock get_installed_languages for predictable testing."""

    def mock_get_langs():
        return {"eng", "fra", "deu", "spa", "ita", "chi_sim", "chi_tra", "jpn", "rus", "por"}

    monkeypatch.setattr(
        "ocrbridge.engines.tesseract.models.get_installed_languages",
        mock_get_langs,
    )


@pytest.fixture
def mock_tesseract_version(monkeypatch):
    """Mock Tesseract version retrieval."""

    def mock_get_version():
        return "5.3.0"

    monkeypatch.setattr("pytesseract.get_tesseract_version", mock_get_version)
