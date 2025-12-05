"""Tests for PDF utilities."""

from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from ocrbridge.core.exceptions import OCRProcessingError
from ocrbridge.core.utils.pdf import convert_pdf_to_images


class TestConvertPDFToImages:
    """Tests for convert_pdf_to_images utility."""

    def test_conversion_success(self, mocker: Any, tmp_path: Path) -> None:
        """Test successful conversion."""
        mock_images = [Image.new("RGB", (100, 100), color="white")]

        # Mock pdf2image.convert_from_path inside the utils module
        mock_convert = mocker.patch(
            "ocrbridge.core.utils.pdf.pdf2image.convert_from_path", return_value=mock_images
        )

        pdf_path = tmp_path / "test.pdf"
        images = convert_pdf_to_images(pdf_path, dpi=150)

        assert images == mock_images
        mock_convert.assert_called_once_with(str(pdf_path), dpi=150, thread_count=2)

    def test_conversion_failure(self, mocker: Any, tmp_path: Path) -> None:
        """Test failure handling."""
        mocker.patch(
            "ocrbridge.core.utils.pdf.pdf2image.convert_from_path",
            side_effect=Exception("Poppler error"),
        )

        pdf_path = tmp_path / "test.pdf"

        with pytest.raises(OCRProcessingError) as exc_info:
            convert_pdf_to_images(pdf_path)

        assert "PDF conversion failed" in str(exc_info.value)
        assert "Poppler error" in str(exc_info.value)
