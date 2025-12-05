"""Tests for TesseractEngine implementation."""

from pathlib import Path

import pytesseract
import pytest
from ocrbridge.core import OCRProcessingError, UnsupportedFormatError
from ocrbridge.core.models import OCREngineParams
from PIL import Image

from ocrbridge.engines.tesseract import TesseractParams


class TestEngineProperties:
    """Test TesseractEngine interface compliance."""

    def test_engine_name(self, tesseract_engine):
        """Test that engine name is correct."""
        assert tesseract_engine.name == "tesseract"

    def test_supported_formats(self, tesseract_engine):
        """Test that supported formats are correct."""
        expected_formats = {".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif"}
        assert tesseract_engine.supported_formats == expected_formats

    def test_supported_formats_lowercase(self, tesseract_engine):
        """Test that all formats are lowercase."""
        for fmt in tesseract_engine.supported_formats:
            assert fmt == fmt.lower()

    def test_supported_formats_include_dot(self, tesseract_engine):
        """Test that all formats include the dot prefix."""
        for fmt in tesseract_engine.supported_formats:
            assert fmt.startswith(".")


class TestProcessImageHappyPath:
    """Test image processing happy path scenarios."""

    def test_process_image_with_defaults(
        self, tesseract_engine, sample_images, mock_tesseract_success, mock_hocr_output
    ):
        """Test processing image with default parameters."""
        result = tesseract_engine.process(sample_images["stock"])

        assert isinstance(result, str)
        assert "ocr_page" in result or "ocr_page" in mock_hocr_output
        assert "<html" in result

    def test_process_image_with_none_params(
        self, tesseract_engine, sample_images, mock_tesseract_success
    ):
        """Test processing image with None params uses defaults."""
        result = tesseract_engine.process(sample_images["stock"], None)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_process_image_with_custom_params(
        self,
        tesseract_engine,
        sample_images,
        mock_tesseract_success,
        monkeypatch,
        mock_installed_languages,
    ):
        """Test processing image with custom parameters."""
        mock_calls = []

        def capture_call(*args, **kwargs):
            mock_calls.append({"args": args, "kwargs": kwargs})
            return b"<html>mock hocr</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", capture_call)

        params = TesseractParams(lang="eng+fra", psm=6, oem=1, dpi=300)
        result = tesseract_engine.process(sample_images["numbers"], params)

        assert isinstance(result, str)
        assert len(mock_calls) == 1
        # Check that language was passed
        assert mock_calls[0]["kwargs"]["lang"] == "eng+fra"
        # Check that config contains psm and oem
        config = mock_calls[0]["kwargs"]["config"]
        assert "--psm 6" in config
        assert "--oem 1" in config

    def test_process_image_returns_string_from_bytes(
        self, tesseract_engine, sample_images, monkeypatch
    ):
        """Test that bytes output from pytesseract is decoded."""

        def mock_return_bytes(*args, **kwargs):
            return b"<html>test hocr</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_return_bytes)

        result = tesseract_engine.process(sample_images["stock"])
        assert isinstance(result, str)
        assert result == "<html>test hocr</html>"

    def test_process_image_returns_string_from_string(
        self, tesseract_engine, sample_images, monkeypatch
    ):
        """Test that string output from pytesseract is returned as-is."""

        def mock_return_string(*args, **kwargs):
            return "<html>test hocr</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_return_string)

        result = tesseract_engine.process(sample_images["stock"])
        assert isinstance(result, str)
        assert result == "<html>test hocr</html>"


class TestProcessPDFHappyPath:
    """Test PDF processing happy path scenarios."""

    def test_process_pdf_single_page(
        self,
        tesseract_engine,
        sample_pdfs,
        mock_pdf_convert_success,
        mock_tesseract_success,
    ):
        """Test processing single-page PDF."""
        result = tesseract_engine.process(sample_pdfs["contract_en_scan"])

        assert isinstance(result, str)
        assert "<html" in result
        assert len(result) > 0

    def test_process_pdf_multi_page(
        self,
        tesseract_engine,
        sample_pdfs,
        mock_pdf_convert_multipage,
        monkeypatch,
        mock_hocr_page,
    ):
        """Test processing multi-page PDF."""
        call_count = 0

        def mock_tesseract_multipage(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_hocr_page.format(call_count, call_count).encode("utf-8")

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_tesseract_multipage)

        result = tesseract_engine.process(sample_pdfs["contract_en_photo"])

        assert isinstance(result, str)
        # Should have called tesseract 3 times (mock returns 3 pages)
        assert call_count == 3
        # Result should contain merged pages
        assert "<body>" in result
        assert "</body>" in result

    def test_process_pdf_with_custom_dpi(
        self,
        tesseract_engine,
        sample_pdfs,
        monkeypatch,
        mock_tesseract_success,
        mock_installed_languages,
    ):
        """Test PDF processing with custom DPI."""
        pdf_convert_calls = []

        def capture_pdf_convert(*args, **kwargs):
            pdf_convert_calls.append({"args": args, "kwargs": kwargs})
            return [Image.new("RGB", (100, 100), color="white")]

        monkeypatch.setattr(
            "ocrbridge.engines.tesseract.engine.convert_pdf_to_images", capture_pdf_convert
        )

        params = TesseractParams(dpi=600)
        tesseract_engine.process(sample_pdfs["contract_en_scan"], params)

        assert len(pdf_convert_calls) == 1
        assert pdf_convert_calls[0]["kwargs"]["dpi"] == 600
        # thread_count is not exposed in convert_pdf_to_images call here, but inside util.
        # We can only check what is passed to convert_pdf_to_images

    def test_process_pdf_default_dpi(
        self, tesseract_engine, sample_pdfs, monkeypatch, mock_tesseract_success
    ):
        """Test PDF processing uses default DPI when not specified."""
        pdf_convert_calls = []

        def capture_pdf_convert(*args, **kwargs):
            pdf_convert_calls.append({"args": args, "kwargs": kwargs})
            return [Image.new("RGB", (100, 100), color="white")]

        monkeypatch.setattr(
            "ocrbridge.engines.tesseract.engine.convert_pdf_to_images", capture_pdf_convert
        )

        tesseract_engine.process(sample_pdfs["contract_en_scan"])

        assert len(pdf_convert_calls) == 1
        # Default DPI for convert_pdf_to_images is 300, matching explicit call in engine.py
        assert pdf_convert_calls[0]["kwargs"]["dpi"] == 300


class TestProcessErrorHandling:
    """Test error handling in process method."""

    def test_unsupported_format_txt(self, tesseract_engine, tmp_path):
        """Test that .txt files raise UnsupportedFormatError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            tesseract_engine.process(txt_file)

        assert ".txt" in str(exc_info.value)
        assert "Supported formats" in str(exc_info.value)

    def test_unsupported_format_docx(self, tesseract_engine, tmp_path):
        """Test that .docx files raise UnsupportedFormatError."""
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("test")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            tesseract_engine.process(docx_file)

        assert ".docx" in str(exc_info.value)

    def test_unsupported_format_bmp(self, tesseract_engine, tmp_path):
        """Test that .bmp files raise UnsupportedFormatError."""
        bmp_file = tmp_path / "test.bmp"
        bmp_file.write_text("test")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            tesseract_engine.process(bmp_file)

        assert ".bmp" in str(exc_info.value)

    def test_wrong_params_type(self, tesseract_engine, sample_images):
        """Test that wrong params type raises TypeError."""
        wrong_params = OCREngineParams()

        with pytest.raises(TypeError) as exc_info:
            tesseract_engine.process(sample_images["stock"], wrong_params)

        assert "requires TesseractParams" in str(exc_info.value)

    def test_tesseract_error_handling(self, tesseract_engine, sample_images, monkeypatch):
        """Test handling of TesseractError."""

        def mock_raise_tesseract_error(*args, **kwargs):
            raise pytesseract.TesseractError(status=1, message="Tesseract failed")

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_raise_tesseract_error)

        with pytest.raises(OCRProcessingError) as exc_info:
            tesseract_engine.process(sample_images["stock"])

        assert "Tesseract engine error" in str(exc_info.value)

    def test_pdf_conversion_error(self, tesseract_engine, sample_pdfs, monkeypatch):
        """Test handling of PDF conversion errors."""

        def mock_raise_conversion_error(*args, **kwargs):
            raise Exception("PDF conversion failed")

        monkeypatch.setattr(
            "ocrbridge.engines.tesseract.engine.convert_pdf_to_images", mock_raise_conversion_error
        )

        with pytest.raises(OCRProcessingError) as exc_info:
            tesseract_engine.process(sample_pdfs["contract_en_scan"])

        assert "PDF conversion failed" in str(exc_info.value)

    def test_generic_processing_error(self, tesseract_engine, sample_images, monkeypatch):
        """Test handling of generic exceptions."""

        def mock_raise_generic_error(*args, **kwargs):
            raise RuntimeError("Something went wrong")

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_raise_generic_error)

        with pytest.raises(OCRProcessingError) as exc_info:
            tesseract_engine.process(sample_images["stock"])

        assert "OCR processing failed" in str(exc_info.value)


class TestProcessAllFormats:
    """Test processing of all supported formats."""

    @pytest.mark.parametrize(
        "extension",
        [".jpg", ".jpeg", ".png", ".tiff", ".tif"],
    )
    def test_process_image_formats(self, tesseract_engine, extension, tmp_path, monkeypatch):
        """Test processing all supported image formats."""
        # Create a simple test image
        test_image = Image.new("RGB", (100, 100), color="white")
        test_file = tmp_path / f"test{extension}"
        test_image.save(test_file)

        def mock_tesseract(*args, **kwargs):
            return b"<html>mock hocr</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_tesseract)

        result = tesseract_engine.process(test_file)
        assert isinstance(result, str)

    def test_process_pdf_format(
        self, tesseract_engine, sample_pdfs, mock_pdf_convert_success, mock_tesseract_success
    ):
        """Test processing PDF format."""
        result = tesseract_engine.process(sample_pdfs["contract_en_scan"])
        assert isinstance(result, str)


class TestInternalMethods:
    """Test internal helper methods."""

    def test_process_image_internal(self, tesseract_engine, monkeypatch):
        """Test _process_image internal method."""
        test_path = Path("/fake/path.jpg")

        def mock_tesseract(*args, **kwargs):
            return b"<html>test hocr</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_tesseract)

        result = tesseract_engine._process_image(test_path, "eng", "--psm 3")
        assert result == "<html>test hocr</html>"

    def test_process_pdf_internal(self, tesseract_engine, monkeypatch):
        """Test _process_pdf internal method."""
        test_path = Path("/fake/path.pdf")

        def mock_convert(*args, **kwargs):
            return [Image.new("RGB", (100, 100), color="white")]

        def mock_tesseract(*args, **kwargs):
            return b"<html>test hocr</html>"

        monkeypatch.setattr(
            "ocrbridge.engines.tesseract.engine.convert_pdf_to_images", mock_convert
        )
        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", mock_tesseract)

        result = tesseract_engine._process_pdf(test_path, "eng", "--psm 3", 300)
        assert isinstance(result, str)
        assert "<html" in result


class TestConfigurationBuilding:
    """Test Tesseract configuration string building."""

    def test_config_all_params(
        self, tesseract_engine, sample_images, monkeypatch, mock_installed_languages
    ):
        """Test config string with all parameters."""
        config_captured = None

        def capture_config(*args, **kwargs):
            nonlocal config_captured
            config_captured = kwargs.get("config", "")
            return b"<html>mock</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", capture_config)

        params = TesseractParams(lang="eng", psm=6, oem=1, dpi=600)
        tesseract_engine.process(sample_images["stock"], params)

        assert "--psm 6" in config_captured
        assert "--oem 1" in config_captured
        assert "--dpi 600" in config_captured

    def test_config_partial_params(
        self, tesseract_engine, sample_images, monkeypatch, mock_installed_languages
    ):
        """Test config string with partial parameters."""
        config_captured = None

        def capture_config(*args, **kwargs):
            nonlocal config_captured
            config_captured = kwargs.get("config", "")
            return b"<html>mock</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", capture_config)

        params = TesseractParams(psm=11, oem=None, dpi=None)
        tesseract_engine.process(sample_images["stock"], params)

        assert "--psm 11" in config_captured
        assert "--oem" not in config_captured or config_captured == "--psm 11"

    def test_config_no_optional_params(
        self, tesseract_engine, sample_images, monkeypatch, mock_installed_languages
    ):
        """Test config string with no optional parameters."""
        config_captured = None

        def capture_config(*args, **kwargs):
            nonlocal config_captured
            config_captured = kwargs.get("config", "")
            return b"<html>mock</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", capture_config)

        params = TesseractParams(lang="eng", psm=None, oem=None, dpi=None)
        tesseract_engine.process(sample_images["stock"], params)

        # Config should be empty or minimal
        assert config_captured == "" or config_captured.strip() == ""

    def test_config_language_parameter(
        self, tesseract_engine, sample_images, monkeypatch, mock_installed_languages
    ):
        """Test that language is passed correctly."""
        lang_captured = None

        def capture_lang(*args, **kwargs):
            nonlocal lang_captured
            lang_captured = kwargs.get("lang", "")
            return b"<html>mock</html>"

        monkeypatch.setattr("pytesseract.image_to_pdf_or_hocr", capture_lang)

        params = TesseractParams(lang="eng+fra")
        tesseract_engine.process(sample_images["stock"], params)

        assert lang_captured == "eng+fra"
