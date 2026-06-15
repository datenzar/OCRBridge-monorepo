"""Tesseract OCR engine parameter models."""

import functools
import logging
import subprocess

from pydantic import Field, field_validator

from ocrbridge.core.models import OCREngineParams
from ocrbridge.core.validation import (
    PATTERN_TESSERACT_LANG_SEGMENT,
    normalize_lowercase,
    validate_list_length,
    validate_regex_pattern,
)

logger = logging.getLogger(__name__)

# Default fallback languages if tesseract --list-langs fails
DEFAULT_TESSERACT_LANGUAGES = {
    "eng",
    "fra",
    "deu",
    "spa",
    "ita",
    "por",
    "rus",
    "ara",
    "chi_sim",
    "jpn",
}

# Constants for language validation
MAX_LANGUAGES = 5


@functools.lru_cache(maxsize=1)
def get_installed_languages() -> set[str]:
    """
    Get list of installed Tesseract language data files.

    Uses subprocess to call 'tesseract --list-langs' and caches the result.
    Fallback to common languages if command fails.

    Returns:
        Set of installed language codes (e.g., {'eng', 'fra', 'deu'})
    """
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Parse output, skip header line "List of available languages (N):"
            langs = result.stdout.strip().split("\n")[1:]
            installed = {lang.strip() for lang in langs if lang.strip()}
            installed.update(DEFAULT_TESSERACT_LANGUAGES)
            return installed
        else:
            # Tesseract binary found but returned error
            logger.warning(
                "Tesseract command failed (exit code %d): %s. Using default languages.",
                result.returncode,
                result.stderr.strip() or "No error message",
            )
            return set(DEFAULT_TESSERACT_LANGUAGES)

    except FileNotFoundError:
        # Tesseract binary not found
        logger.warning(
            "Tesseract binary not found. Install Tesseract OCR to enable language detection. "
            "Using default languages: %s",
            ", ".join(sorted(DEFAULT_TESSERACT_LANGUAGES)),
        )
        return set(DEFAULT_TESSERACT_LANGUAGES)

    except subprocess.TimeoutExpired:
        logger.warning("Tesseract language detection timed out. Using default languages.")
        return set(DEFAULT_TESSERACT_LANGUAGES)

    except Exception as e:
        logger.warning(
            "Unexpected error detecting Tesseract languages: %s. Using default languages.",
            str(e),
        )
        return set(DEFAULT_TESSERACT_LANGUAGES)


class TesseractParams(OCREngineParams):
    """Tesseract OCR engine parameters with validation."""

    lang: str | None = Field(
        default="eng",
        pattern=r"^[a-z_]{3,7}(\+[a-z_]{3,7})*$",
        description=f"Language code(s): 'eng', 'fra', 'eng+fra' (max {MAX_LANGUAGES} languages)",
        examples=["eng", "eng+fra", "eng+fra+deu"],
    )

    psm: int | None = Field(
        default=3,
        ge=0,
        le=13,
        description="Page segmentation mode (0-13)",
    )

    oem: int | None = Field(
        default=1,
        ge=0,
        le=3,
        description="OCR Engine mode: 0=Legacy, 1=LSTM, 2=Both, 3=Default",
    )

    dpi: int | None = Field(
        default=300, ge=70, le=2400, description="Image DPI for PDF conversion (70-2400)"
    )

    @field_validator("lang", mode="before")
    @classmethod
    def normalize_language(cls, v: str | None) -> str | None:
        """Normalize language codes to lowercase and trim whitespace."""
        return normalize_lowercase(v)

    @field_validator("lang", mode="after")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        """Validate language count, format, and availability."""
        if v is None:
            return v

        # Split and validate count
        langs = v.split("+")
        validate_list_length(langs, max_length=MAX_LANGUAGES, field_name="languages")

        # Validate each segment format using core pattern
        for lang in langs:
            validate_regex_pattern(
                lang,
                PATTERN_TESSERACT_LANG_SEGMENT,
                f"Language '{lang}' must be 3-7 lowercase letters or underscores "
                f"(e.g., 'eng', 'chi_sim')",
            )

        # Engine-specific: Check against installed languages
        installed = get_installed_languages()
        invalid = [lang for lang in langs if lang not in installed]

        if invalid:
            available_sample = ", ".join(sorted(installed)[:10])
            raise ValueError(
                f"Language(s) not installed: {', '.join(invalid)}. Available: {available_sample}..."
            )

        return v
