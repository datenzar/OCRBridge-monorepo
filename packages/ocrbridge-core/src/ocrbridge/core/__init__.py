"""OCR Bridge Core - Base interfaces and utilities for OCR engines."""

from .base import OCREngine
from .exceptions import (
    EngineNotAvailableError,
    InvalidParametersError,
    OCRBridgeError,
    OCRProcessingError,
    UnsupportedFormatError,
)
from .models import OCREngineParams
from .validation import (
    PATTERN_FILE_EXTENSION,
    PATTERN_IETF_BCP47,
    PATTERN_ISO_639_1,
    PATTERN_ISO_639_2,
    PATTERN_TESSERACT_LANG_SEGMENT,
    create_split_string_validator,
    normalize_language_list,
    normalize_lowercase,
    validate_float_range,
    validate_int_range,
    validate_language_code_format,
    validate_list_length,
    validate_probability,
    validate_regex_pattern,
    validate_whitelist,
)

__all__ = [
    # Base classes
    "OCREngine",
    "OCREngineParams",
    # Exceptions
    "EngineNotAvailableError",
    "InvalidParametersError",
    "OCRBridgeError",
    "OCRProcessingError",
    "UnsupportedFormatError",
    # Validation utilities - Regex validators
    "validate_regex_pattern",
    "validate_language_code_format",
    # Validation utilities - Numeric validators
    "validate_int_range",
    "validate_float_range",
    "validate_probability",
    # Validation utilities - List validators
    "validate_list_length",
    "validate_whitelist",
    # Validation utilities - Normalization
    "normalize_lowercase",
    "normalize_language_list",
    # Validation utilities - Composite validators
    "create_split_string_validator",
    # Validation utilities - Common patterns
    "PATTERN_IETF_BCP47",
    "PATTERN_TESSERACT_LANG_SEGMENT",
    "PATTERN_ISO_639_1",
    "PATTERN_ISO_639_2",
    "PATTERN_FILE_EXTENSION",
]

__version__ = "3.1.0"
