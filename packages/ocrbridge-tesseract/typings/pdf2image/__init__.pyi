from __future__ import annotations

from pathlib import Path, PurePath

from PIL.Image import Image


def convert_from_path(
    pdf_path: str | Path | PurePath,
    dpi: int = ...,
    thread_count: int = ...,  # noqa: DAR401
    poppler_path: str | Path | PurePath | None = ...,  # noqa: DAR401
    timeout: int | None = ...,  # noqa: DAR401
) -> list[Image]:
    ...
