"""Unit tests for EasyOCR engine with mocked dependencies."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from ocrbridge.core import OCRProcessingError, UnsupportedFormatError
from PIL import Image

from ocrbridge.engines.easyocr import EasyOCREngine, EasyOCRParams


class TestEasyOCREngineProperties:
    """Test suite for EasyOCREngine properties."""

    def test_name_property(self) -> None:
        """Test engine name property returns 'easyocr'."""
        engine = EasyOCREngine()
        assert engine.name == "easyocr"

    def test_supported_formats_property(self) -> None:
        """Test supported_formats returns correct set of extensions."""
        engine = EasyOCREngine()
        expected_formats = {".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif"}
        assert engine.supported_formats == expected_formats

    def test_initialization(self) -> None:
        """Test engine initializes with None reader and languages."""
        engine = EasyOCREngine()
        assert engine.reader is None
        assert engine._current_languages is None


class TestCoerceParams:
    """Test suite for _coerce_params method."""

    def test_coerce_none_returns_default(self) -> None:
        """Test _coerce_params with None returns default EasyOCRParams."""
        engine = EasyOCREngine()
        params = engine._coerce_params(None)

        assert isinstance(params, EasyOCRParams)
        assert params.languages == ["en"]
        assert params.text_threshold == 0.7

    def test_coerce_easyocr_params_returns_same(self) -> None:
        """Test _coerce_params with EasyOCRParams returns same instance."""
        engine = EasyOCREngine()
        original_params = EasyOCRParams(languages=["en", "de"])

        params = engine._coerce_params(original_params)

        assert params is original_params

    def test_coerce_compatible_params_converts(self) -> None:
        """Test _coerce_params converts compatible params with model_dump."""
        engine = EasyOCREngine()

        # Create a mock params object with model_dump method
        mock_params = Mock()
        mock_params.model_dump.return_value = {
            "languages": ["fr", "de"],
            "text_threshold": 0.8,
            "link_threshold": 0.6,
        }

        params = engine._coerce_params(mock_params)

        assert isinstance(params, EasyOCRParams)
        assert params.languages == ["fr", "de"]
        assert params.text_threshold == 0.8
        assert params.link_threshold == 0.6

    def test_coerce_incompatible_params_raises_error(self) -> None:
        """Test _coerce_params raises error for incompatible params."""
        engine = EasyOCREngine()

        # Create params without model_dump method
        mock_params = Mock(spec=[])  # No methods

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._coerce_params(mock_params)

        assert "EasyOCR engine requires EasyOCRParams" in str(exc_info.value)


class TestCreateReader:
    """Test suite for _create_reader method."""

    def test_create_reader_with_languages(self, mocker: Any) -> None:
        """Test _create_reader creates reader with specified languages."""
        engine = EasyOCREngine()

        # Mock easyocr.Reader
        mock_reader_class = mocker.patch("easyocr.Reader")
        mock_reader_instance = MagicMock()
        mock_reader_class.return_value = mock_reader_instance

        # Mock get_easyocr_device
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.get_easyocr_device",
            return_value=(False, "cpu"),
        )

        reader = engine._create_reader(["en", "de"])

        assert reader is mock_reader_instance
        mock_reader_class.assert_called_once_with(lang_list=["en", "de"], gpu=False)

    def test_create_reader_with_gpu(self, mocker: Any) -> None:
        """Test _create_reader respects GPU availability."""
        engine = EasyOCREngine()

        mock_reader_class = mocker.patch("easyocr.Reader")
        mock_reader_instance = MagicMock()
        mock_reader_class.return_value = mock_reader_instance

        # Mock GPU available
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.get_easyocr_device",
            return_value=(True, "cuda:0"),
        )

        engine._create_reader(["en"])

        mock_reader_class.assert_called_once_with(lang_list=["en"], gpu=True)

    def test_create_reader_easyocr_not_installed(self, mocker: Any) -> None:
        """Test _create_reader raises error when easyocr not installed."""
        engine = EasyOCREngine()

        # Mock ImportError when importing easyocr
        mocker.patch("builtins.__import__", side_effect=ImportError("No module named 'easyocr'"))

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._create_reader(["en"])

        assert "EasyOCR not installed" in str(exc_info.value)


class TestProcessImage:
    """Test suite for _process_image method."""

    def test_process_image_success(self, mocker: Any, tmp_path: Path) -> None:
        """Test _process_image processes image successfully."""
        engine = EasyOCREngine()

        # Create a mock reader
        mock_reader = MagicMock()
        mock_results = [
            ([[10, 10], [100, 10], [100, 50], [10, 50]], "Test", 0.95),
        ]
        mock_reader.readtext.return_value = mock_results
        engine.reader = mock_reader

        # Create a temporary test image
        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        # Mock _to_hocr method
        mock_to_hocr = mocker.patch.object(
            engine,
            "_to_hocr",
            return_value="<hocr>mock output</hocr>",
        )

        params = EasyOCRParams()
        result = engine._process_image(test_image, params)

        assert result == "<hocr>mock output</hocr>"
        mock_reader.readtext.assert_called_once_with(
            str(test_image),
            detail=1,
            paragraph=False,
        )
        mock_to_hocr.assert_called_once_with(mock_results, test_image)

    def test_process_image_no_reader_raises_error(self) -> None:
        """Test _process_image raises error when reader is None."""
        engine = EasyOCREngine()
        engine.reader = None

        params = EasyOCRParams()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._process_image(Path("/fake/path.jpg"), params)

        assert "reader is not initialized" in str(exc_info.value)


class TestProcessPDF:
    """Test suite for _process_pdf method."""

    def test_process_pdf_single_page(self, mocker: Any, tmp_path: Path) -> None:
        """Test _process_pdf processes single-page PDF."""
        engine = EasyOCREngine()

        # Mock reader
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            ([[10, 10], [100, 10], [100, 50], [10, 50]], "Page 1", 0.95),
        ]
        engine.reader = mock_reader

        # Mock convert_pdf_to_images
        mock_image = Image.new("RGB", (800, 600), color="white")
        mock_convert = mocker.patch(
            "ocrbridge.engines.easyocr.engine.convert_pdf_to_images",
            return_value=[mock_image],
        )

        # Mock _to_hocr
        mocker.patch.object(
            engine,
            "_to_hocr",
            return_value="<hocr>page 1</hocr>",
        )

        # Mock numpy.array
        mocker.patch("ocrbridge.engines.easyocr.engine.np.array", return_value="mock_array")

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()  # Create empty file

        params = EasyOCRParams()
        result = engine._process_pdf(pdf_path, params)

        assert result == "<hocr>page 1</hocr>"
        mock_convert.assert_called_once_with(pdf_path, dpi=300)

    def test_process_pdf_multiple_pages(self, mocker: Any, tmp_path: Path) -> None:
        """Test _process_pdf processes multi-page PDF."""
        engine = EasyOCREngine()

        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            ([[10, 10], [100, 10], [100, 50], [10, 50]], "Text", 0.95),
        ]
        engine.reader = mock_reader

        # Mock convert_pdf_to_images with 3 pages
        mock_images = [
            Image.new("RGB", (800, 600), color="white"),
            Image.new("RGB", (800, 600), color="white"),
            Image.new("RGB", (800, 600), color="white"),
        ]
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.convert_pdf_to_images",
            return_value=mock_images,
        )

        # Mock _to_hocr to return different content per page
        page_hocrs = ["<hocr>page 1</hocr>", "<hocr>page 2</hocr>", "<hocr>page 3</hocr>"]
        mocker.patch.object(engine, "_to_hocr", side_effect=page_hocrs)

        # Mock merge_hocr_pages
        mock_merge = mocker.patch(
            "ocrbridge.engines.easyocr.engine.merge_hocr_pages",
            return_value="<hocr>merged</hocr>",
        )

        mocker.patch("ocrbridge.engines.easyocr.engine.np.array", return_value="mock_array")

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        params = EasyOCRParams()
        result = engine._process_pdf(pdf_path, params)

        assert result == "<hocr>merged</hocr>"
        mock_merge.assert_called_once_with(page_hocrs, system_name="easyocr")

    def test_process_pdf_conversion_failure(self, mocker: Any, tmp_path: Path) -> None:
        """Test _process_pdf raises error on PDF conversion failure."""
        engine = EasyOCREngine()
        engine.reader = MagicMock()

        # Mock convert_pdf_to_images to raise exception
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.convert_pdf_to_images",
            side_effect=OCRProcessingError("PDF conversion failed"),
        )

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        params = EasyOCRParams()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._process_pdf(pdf_path, params)

        assert "PDF conversion failed" in str(exc_info.value)

    def test_process_pdf_no_reader_raises_error(self, mocker: Any, tmp_path: Path) -> None:
        """Test _process_pdf raises error when reader is None."""
        engine = EasyOCREngine()
        engine.reader = None

        mock_image = Image.new("RGB", (800, 600), color="white")
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.convert_pdf_to_images",
            return_value=[mock_image],
        )

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        params = EasyOCRParams()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine._process_pdf(pdf_path, params)

        assert "reader is not initialized" in str(exc_info.value)


class TestToHOCR:
    """Test suite for _to_hocr method."""

    def test_to_hocr_with_valid_image(self, mocker: Any, tmp_path: Path) -> None:
        """Test _to_hocr converts results using image dimensions."""
        engine = EasyOCREngine()

        # Create test image
        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), color="white")
        img.save(test_image)

        # Mock easyocr_to_hocr from core
        mock_converter = mocker.patch(
            "ocrbridge.engines.easyocr.hocr.to_hocr",
            return_value="<hocr>converted</hocr>",
        )

        easyocr_results = [
            ([[10, 10], [100, 10], [100, 50], [10, 50]], "Test", 0.95),
        ]

        result = engine._to_hocr(easyocr_results, test_image)

        assert result == "<hocr>converted</hocr>"
        mock_converter.assert_called_once_with(easyocr_results, 800, 600)

    def test_to_hocr_with_invalid_image_uses_defaults(self, mocker: Any) -> None:
        """Test _to_hocr uses default dimensions when image can't be opened."""
        engine = EasyOCREngine()

        # Mock easyocr_to_hocr from core
        mock_converter = mocker.patch(
            "ocrbridge.engines.easyocr.hocr.to_hocr",
            return_value="<hocr>converted</hocr>",
        )

        easyocr_results = [
            ([[10, 10], [100, 10], [100, 50], [10, 50]], "Test", 0.95),
        ]

        # Use non-existent path
        result = engine._to_hocr(easyocr_results, Path("/nonexistent/image.jpg"))

        assert result == "<hocr>converted</hocr>"
        # Should use default dimensions 1000x1000
        mock_converter.assert_called_once_with(easyocr_results, 1000, 1000)


class TestProcess:
    """Test suite for main process method."""

    def test_process_nonexistent_file_raises_error(self) -> None:
        """Test process raises error for non-existent file."""
        engine = EasyOCREngine()

        with pytest.raises(OCRProcessingError) as exc_info:
            engine.process(Path("/nonexistent/file.jpg"))

        assert "File not found" in str(exc_info.value)

    def test_process_unsupported_format_raises_error(self, tmp_path: Path) -> None:
        """Test process raises error for unsupported file format."""
        engine = EasyOCREngine()

        # Create a file with unsupported extension
        unsupported_file = tmp_path / "test.txt"
        unsupported_file.touch()

        with pytest.raises(UnsupportedFormatError) as exc_info:
            engine.process(unsupported_file)

        assert "Unsupported file format: .txt" in str(exc_info.value)

    def test_process_creates_reader_on_first_use(self, mocker: Any, tmp_path: Path) -> None:
        """Test process creates reader on first use."""
        engine = EasyOCREngine()

        # Create test image
        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        # Mock _create_reader
        mock_reader = MagicMock()
        mock_create = mocker.patch.object(engine, "_create_reader", return_value=mock_reader)

        # Mock _process_image
        mocker.patch.object(engine, "_process_image", return_value="<hocr>test</hocr>")

        result = engine.process(test_image)

        assert result == "<hocr>test</hocr>"
        mock_create.assert_called_once_with(["en"])  # Default language
        assert engine.reader is mock_reader
        assert engine._current_languages == ["en"]

    def test_process_reuses_reader_same_language(self, mocker: Any, tmp_path: Path) -> None:
        """Test process reuses reader for same language."""
        engine = EasyOCREngine()

        # Set up existing reader
        mock_reader = MagicMock()
        engine.reader = mock_reader
        engine._current_languages = ["en"]

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        mock_create = mocker.patch.object(engine, "_create_reader")
        mocker.patch.object(engine, "_process_image", return_value="<hocr>test</hocr>")

        result = engine.process(test_image, EasyOCRParams(languages=["en"]))

        assert result == "<hocr>test</hocr>"
        mock_create.assert_not_called()  # Should not create new reader

    def test_process_recreates_reader_different_language(self, mocker: Any, tmp_path: Path) -> None:
        """Test process recreates reader when languages change."""
        engine = EasyOCREngine()

        # Set up existing reader with English
        old_reader = MagicMock()
        engine.reader = old_reader
        engine._current_languages = ["en"]

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        # Mock new reader creation
        new_reader = MagicMock()
        mock_create = mocker.patch.object(engine, "_create_reader", return_value=new_reader)
        mocker.patch.object(engine, "_process_image", return_value="<hocr>test</hocr>")

        result = engine.process(test_image, EasyOCRParams(languages=["de", "fr"]))

        assert result == "<hocr>test</hocr>"
        mock_create.assert_called_once_with(["de", "fr"])
        assert engine.reader is new_reader
        assert engine._current_languages == ["de", "fr"]

    def test_process_routes_to_process_image_for_jpg(self, mocker: Any, tmp_path: Path) -> None:
        """Test process routes to _process_image for JPEG files."""
        engine = EasyOCREngine()

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        mocker.patch.object(engine, "_create_reader", return_value=MagicMock())
        mock_process_image = mocker.patch.object(
            engine,
            "_process_image",
            return_value="<hocr>image</hocr>",
        )
        mock_process_pdf = mocker.patch.object(engine, "_process_pdf")

        result = engine.process(test_image)

        assert result == "<hocr>image</hocr>"
        mock_process_image.assert_called_once()
        mock_process_pdf.assert_not_called()

    def test_process_routes_to_process_pdf_for_pdf(self, mocker: Any, tmp_path: Path) -> None:
        """Test process routes to _process_pdf for PDF files."""
        engine = EasyOCREngine()

        test_pdf = tmp_path / "test.pdf"
        test_pdf.touch()

        mocker.patch.object(engine, "_create_reader", return_value=MagicMock())
        mock_process_image = mocker.patch.object(engine, "_process_image")
        mock_process_pdf = mocker.patch.object(
            engine,
            "_process_pdf",
            return_value="<hocr>pdf</hocr>",
        )

        result = engine.process(test_pdf)

        assert result == "<hocr>pdf</hocr>"
        mock_process_pdf.assert_called_once()
        mock_process_image.assert_not_called()

    def test_process_handles_default_params(self, mocker: Any, tmp_path: Path) -> None:
        """Test process handles None params correctly."""
        engine = EasyOCREngine()

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (200, 100), color="white")
        img.save(test_image)

        mocker.patch.object(engine, "_create_reader", return_value=MagicMock())
        mocker.patch.object(engine, "_process_image", return_value="<hocr>test</hocr>")

        # Pass None for params
        result = engine.process(test_image, None)

        assert result == "<hocr>test</hocr>"
        assert engine._current_languages == ["en"]  # Should use default
