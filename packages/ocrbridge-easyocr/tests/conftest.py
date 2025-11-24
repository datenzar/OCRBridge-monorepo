"""Shared pytest fixtures for ocrbridge-easyocr tests."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ocrbridge.engines.easyocr import EasyOCRParams


@pytest.fixture
def samples_dir() -> Path:
    """Return the path to the samples directory."""
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def sample_jpg_stock(samples_dir: Path) -> Path:
    """Return path to stock grayscale JPEG sample."""
    return samples_dir / "stock_gs200.jpg"


@pytest.fixture
def sample_jpg_numbers(samples_dir: Path) -> Path:
    """Return path to numbers grayscale JPEG sample."""
    return samples_dir / "numbers_gs150.jpg"


@pytest.fixture
def sample_pdf_en_scan(samples_dir: Path) -> Path:
    """Return path to English scanned contract PDF."""
    return samples_dir / "contract_en_scan.pdf"


@pytest.fixture
def sample_pdf_en_photo(samples_dir: Path) -> Path:
    """Return path to English photographed contract PDF."""
    return samples_dir / "contract_en_photo.pdf"


@pytest.fixture
def sample_pdf_de_scan(samples_dir: Path) -> Path:
    """Return path to German scanned contract PDF."""
    return samples_dir / "contract_de_scan.pdf"


@pytest.fixture
def sample_pdf_de_photo(samples_dir: Path) -> Path:
    """Return path to German photographed contract PDF."""
    return samples_dir / "contract_de_photo.pdf"


@pytest.fixture
def default_params() -> EasyOCRParams:
    """Return default EasyOCRParams instance."""
    return EasyOCRParams()


@pytest.fixture
def custom_params() -> EasyOCRParams:
    """Return EasyOCRParams with custom settings."""
    return EasyOCRParams(
        languages=["en", "de"],
        text_threshold=0.8,
        link_threshold=0.6,
    )


@pytest.fixture
def mock_easyocr_reader(mocker: Any) -> MagicMock:
    """Return a mocked EasyOCR Reader instance."""
    mock_reader = MagicMock()
    # Mock readtext method to return sample results
    mock_reader.readtext.return_value = [
        (
            [[10, 10], [100, 10], [100, 50], [10, 50]],  # bounding box
            "Sample Text",  # detected text
            0.95,  # confidence
        ),
        (
            [[10, 60], [150, 60], [150, 100], [10, 100]],
            "Another Line",
            0.88,
        ),
    ]
    return mock_reader


@pytest.fixture
def mock_easyocr_class(mocker: Any, mock_easyocr_reader: MagicMock) -> MagicMock:
    """Mock the easyocr.Reader class to return a mock reader."""
    mock_class = mocker.patch("easyocr.Reader", return_value=mock_easyocr_reader)
    return mock_class


@pytest.fixture
def mock_torch_cuda_available(mocker: Any) -> MagicMock:
    """Mock torch.cuda.is_available() to return True."""
    return mocker.patch("torch.cuda.is_available", return_value=True)


@pytest.fixture
def mock_torch_cuda_unavailable(mocker: Any) -> MagicMock:
    """Mock torch.cuda.is_available() to return False."""
    return mocker.patch("torch.cuda.is_available", return_value=False)


@pytest.fixture
def mock_pdf2image(mocker: Any) -> MagicMock:
    """Mock pdf2image.convert_from_path to return PIL Image objects."""
    from PIL import Image

    # Create a simple test image
    mock_image = Image.new("RGB", (800, 600), color="white")
    mock_convert = mocker.patch("pdf2image.convert_from_path", return_value=[mock_image])
    return mock_convert


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create and return a temporary directory for test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
