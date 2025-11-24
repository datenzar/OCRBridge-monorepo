from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL.Image import Image


class TesseractError(Exception):
    ...


def image_to_pdf_or_hocr(
    image: Path | str | Image,
    lang: str | None = ...,  # noqa: DAR401
    config: str = ...,  # noqa: DAR401
    nice: int = ...,  # noqa: DAR401
    extension: str = ...,  # noqa: DAR401
    timeout: int | None = ...,  # noqa: DAR401
) -> bytes | str:
    ...


def get_tesseract_version() -> str:
    ...
