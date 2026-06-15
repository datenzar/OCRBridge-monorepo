"""Integration tests for TesseractEngine with real Tesseract binary.

These tests require Tesseract to be installed on the system.
They are marked with @pytest.mark.integration and will be skipped if Tesseract is not available.
"""

import shutil
import subprocess

import pytest

from ocrbridge.engines.tesseract import TesseractEngine, TesseractParams


def has_tesseract():
    """Check if Tesseract binary is available on the system."""
    return shutil.which("tesseract") is not None


def has_language(lang_code):
    """Check if a specific Tesseract language pack is installed."""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return lang_code in result.stdout
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


pytestmark = pytest.mark.integration


@pytest.mark.skipif(not has_tesseract(), reason="Tesseract not installed")
class TestRealImageProcessing:
    """Test real image processing with Tesseract binary."""

    def test_process_real_jpg_image(self, sample_images):
        """Test processing a real JPG image with Tesseract."""
        engine = TesseractEngine()
        result = engine.process(sample_images["stock"])

        assert isinstance(result, str)
        assert len(result) > 0
        # Check for HOCR structure
        assert "<html" in result or "<?xml" in result
        assert "ocr" in result.lower()

    def test_process_real_jpg_with_custom_params(self, sample_images):
        """Test processing with custom parameters."""
        engine = TesseractEngine()
        params = TesseractParams(lang="eng", psm=6, oem=1, dpi=300)
        result = engine.process(sample_images["numbers"], params)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("psm_mode", [3, 6, 11])
    def test_different_psm_modes(self, sample_images, psm_mode):
        """Test different PSM modes on the same image."""
        engine = TesseractEngine()
        params = TesseractParams(psm=psm_mode)
        result = engine.process(sample_images["stock"], params)

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.skipif(not has_tesseract(), reason="Tesseract not installed")
class TestRealPDFProcessing:
    """Test real PDF processing with Tesseract binary."""

    def test_process_real_pdf(self, sample_pdfs):
        """Test processing a real PDF file."""
        engine = TesseractEngine()
        result = engine.process(sample_pdfs["contract_en_scan"])

        assert isinstance(result, str)
        assert len(result) > 0
        assert "<html" in result or "<?xml" in result

    def test_process_pdf_with_high_dpi(self, sample_pdfs):
        """Test PDF processing with high DPI."""
        engine = TesseractEngine()
        params = TesseractParams(dpi=600)
        result = engine.process(sample_pdfs["contract_en_scan"], params)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_pdf_with_low_dpi(self, sample_pdfs):
        """Test PDF processing with low DPI for speed."""
        engine = TesseractEngine()
        params = TesseractParams(dpi=150)
        result = engine.process(sample_pdfs["contract_en_scan"], params)

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.skipif(not has_tesseract(), reason="Tesseract not installed")
@pytest.mark.skipif(not has_language("deu"), reason="German language pack not installed")
class TestMultilingualProcessing:
    """Test multilingual processing with real Tesseract binary."""

    def test_process_german_pdf(self, sample_pdfs):
        """Test processing a German PDF with German language pack."""
        engine = TesseractEngine()
        params = TesseractParams(lang="deu")
        result = engine.process(sample_pdfs["contract_de_scan"], params)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.skipif(not has_language("fra"), reason="French language pack not installed")
    def test_process_multilingual(self, sample_pdfs):
        """Test processing with multiple languages."""
        engine = TesseractEngine()
        params = TesseractParams(lang="eng+deu")
        result = engine.process(sample_pdfs["contract_en_scan"], params)

        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.skipif(not has_tesseract(), reason="Tesseract not installed")
class TestRealHOCROutput:
    """Test HOCR output structure from real Tesseract."""

    def test_hocr_contains_page_info(self, sample_images):
        """Test that HOCR output contains page information."""
        engine = TesseractEngine()
        result = engine.process(sample_images["stock"])

        # Check for typical HOCR elements
        assert "ocr_page" in result or "ocrx_block" in result

    def test_hocr_contains_metadata(self, sample_images):
        """Test that HOCR output contains metadata."""
        engine = TesseractEngine()
        result = engine.process(sample_images["stock"])

        # Should contain meta information
        assert "tesseract" in result.lower() or "ocr-system" in result.lower()

    def test_hocr_well_formed_xml(self, sample_images):
        """Test that HOCR output is well-formed XML/HTML."""
        engine = TesseractEngine()
        result = engine.process(sample_images["stock"])

        # Basic XML/HTML structure checks
        assert "<html" in result or "<?xml" in result
        assert "</html>" in result
        assert "<body" in result
        assert "</body>" in result


@pytest.mark.skipif(not has_tesseract(), reason="Tesseract not installed")
@pytest.mark.slow
class TestLargeFileProcessing:
    """Test processing of larger/complex files (marked as slow)."""

    def test_process_photo_pdf(self, sample_pdfs):
        """Test processing a photo-based PDF (potentially larger)."""
        engine = TesseractEngine()
        result = engine.process(sample_pdfs["contract_en_photo"])

        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_german_photo_pdf(self, sample_pdfs):
        """Test processing German photo PDF."""
        engine = TesseractEngine()

        # Use German if available, otherwise fall back to English
        if has_language("deu"):
            params = TesseractParams(lang="deu")
        else:
            params = TesseractParams(lang="eng")

        result = engine.process(sample_pdfs["contract_de_photo"], params)

        assert isinstance(result, str)
        assert len(result) > 0
