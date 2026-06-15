"""Integration tests for EasyOCR engine with real OCR processing.

These tests require EasyOCR to be installed and will actually run OCR on sample files.
They are marked as integration tests and may be slower than unit tests.
"""

from pathlib import Path

import pytest

from ocrbridge.engines.easyocr import EasyOCREngine, EasyOCRParams


@pytest.mark.integration
class TestEasyOCREngineIntegration:
    """Integration tests using real EasyOCR processing."""

    def test_process_jpeg_image_english(self, sample_jpg_stock: Path) -> None:
        """Test processing a JPEG image with English text."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        result = engine.process(sample_jpg_stock, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "<body>" in result
        assert "</body>" in result
        assert "</html>" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_jpeg_image_numbers(self, sample_jpg_numbers: Path) -> None:
        """Test processing a JPEG image with numbers."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        result = engine.process(sample_jpg_numbers, params)

        # Verify valid HOCR output
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_pdf_english_scan(self, sample_pdf_en_scan: Path) -> None:
        """Test processing an English scanned PDF."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        result = engine.process(sample_pdf_en_scan, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "<body>" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_pdf_english_photo(self, sample_pdf_en_photo: Path) -> None:
        """Test processing an English photographed PDF."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        result = engine.process(sample_pdf_en_photo, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_pdf_german_scan(self, sample_pdf_de_scan: Path) -> None:
        """Test processing a German scanned PDF."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["de"])

        result = engine.process(sample_pdf_de_scan, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_pdf_german_photo(self, sample_pdf_de_photo: Path) -> None:
        """Test processing a German photographed PDF."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["de"])

        result = engine.process(sample_pdf_de_photo, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_with_multiple_languages(self, sample_jpg_stock: Path) -> None:
        """Test processing with multiple language support."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en", "de"])

        result = engine.process(sample_jpg_stock, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result
        assert "ocr-system" in result or "easyocr" in result.lower()

    def test_process_with_custom_thresholds(self, sample_jpg_stock: Path) -> None:
        """Test processing with custom confidence thresholds."""
        engine = EasyOCREngine()
        params = EasyOCRParams(
            languages=["en"],
            text_threshold=0.8,
            link_threshold=0.6,
        )

        result = engine.process(sample_jpg_stock, params)

        # Verify HOCR structure
        assert result.startswith('<?xml version="1.0"')
        assert "<html" in result

    def test_reader_reuse_same_language(
        self, sample_jpg_stock: Path, sample_jpg_numbers: Path
    ) -> None:
        """Test that reader is reused for same language across multiple files."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        # Process first image
        result1 = engine.process(sample_jpg_stock, params)
        reader1 = engine.reader

        # Process second image with same language
        result2 = engine.process(sample_jpg_numbers, params)
        reader2 = engine.reader

        # Reader should be the same instance
        assert reader1 is reader2
        assert result1.startswith('<?xml version="1.0"')
        assert result2.startswith('<?xml version="1.0"')

    def test_reader_recreated_different_language(
        self, sample_pdf_en_scan: Path, sample_pdf_de_scan: Path
    ) -> None:
        """Test that reader is recreated when language changes."""
        engine = EasyOCREngine()

        # Process with English
        params_en = EasyOCRParams(languages=["en"])
        result1 = engine.process(sample_pdf_en_scan, params_en)
        reader1 = engine.reader

        # Process with German (should recreate reader)
        params_de = EasyOCRParams(languages=["de"])
        result2 = engine.process(sample_pdf_de_scan, params_de)
        reader2 = engine.reader

        # Reader should be different instances
        assert reader1 is not reader2
        assert result1.startswith('<?xml version="1.0"')
        assert result2.startswith('<?xml version="1.0"')

    def test_hocr_contains_text_boxes(self, sample_jpg_stock: Path) -> None:
        """Test that HOCR output contains text box elements."""
        engine = EasyOCREngine()
        params = EasyOCRParams(languages=["en"])

        result = engine.process(sample_jpg_stock, params)

        # HOCR should contain structural elements
        # The exact structure depends on easyocr_to_hocr implementation
        # but should have basic HOCR structure
        assert "<body>" in result
        assert result.count("<") > 10  # Should have multiple elements


@pytest.mark.integration
@pytest.mark.slow
class TestEasyOCREngineSlowIntegration:
    """Slower integration tests for heavy operations."""

    def test_process_all_sample_files_sequentially(
        self,
        sample_jpg_stock: Path,
        sample_jpg_numbers: Path,
        sample_pdf_en_scan: Path,
        sample_pdf_de_scan: Path,
    ) -> None:
        """Test processing multiple files in sequence."""
        engine = EasyOCREngine()

        # Process different file types
        files_and_langs = [
            (sample_jpg_stock, ["en"]),
            (sample_jpg_numbers, ["en"]),
            (sample_pdf_en_scan, ["en"]),
            (sample_pdf_de_scan, ["de"]),
        ]

        results = []
        for file_path, languages in files_and_langs:
            params = EasyOCRParams(languages=languages)
            result = engine.process(file_path, params)
            results.append(result)

        # All results should be valid HOCR
        assert len(results) == 4
        for result in results:
            assert result.startswith('<?xml version="1.0"')
            assert "<html" in result
