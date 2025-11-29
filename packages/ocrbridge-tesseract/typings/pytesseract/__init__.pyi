from __future__ import annotations

from pathlib import Path

from PIL.Image import Image

class TesseractError(Exception): ...

def image_to_pdf_or_hocr(
    image: Path | str | Image,
    lang: str | None = ...,
    config: str = ...,
    nice: int = ...,
    extension: str = ...,
    timeout: int | None = ...,
) -> bytes | str: ...
def get_tesseract_version() -> str: ...
