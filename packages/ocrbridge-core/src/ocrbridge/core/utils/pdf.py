"""PDF processing utilities."""

from pathlib import Path
from typing import Any, cast

import pdf2image as _pdf2image
from PIL import Image

from ocrbridge.core.exceptions import OCRProcessingError

# Type cast for pdf2image because it doesn't have type stubs
pdf2image = cast(Any, _pdf2image)


def convert_pdf_to_images(
    pdf_path: Path, dpi: int = 300, thread_count: int = 2
) -> list[Image.Image]:
    """Convert PDF file to a list of PIL Images.

    Args:
        pdf_path: Path to the PDF file.
        dpi: DPI for conversion (default: 300).
        thread_count: Number of threads to use (default: 2).

    Returns:
        List of PIL Image objects (one per page).

    Raises:
        OCRProcessingError: If conversion fails.
    """
    try:
        # Cast return type since pdf2image is untyped
        images = cast(
            list[Image.Image],
            pdf2image.convert_from_path(str(pdf_path), dpi=dpi, thread_count=thread_count),
        )
        return images
    except Exception as e:
        raise OCRProcessingError(f"PDF conversion failed: {str(e)}") from e
