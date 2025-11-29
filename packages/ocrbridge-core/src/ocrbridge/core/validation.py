"""Validation utilities for OCR engine parameters.

This module provides reusable validation functions for common parameter patterns
across OCR engines. Engines define their own Pydantic models and constraints,
using these utilities to reduce code duplication.

All validators are designed to work seamlessly with Pydantic @field_validator
decorators while also being usable standalone.
"""

import re
from typing import Callable, Pattern, TypeVar

T = TypeVar("T")


# ============================================================================
# Regex Pattern Validators
# ============================================================================


def validate_regex_pattern(
    value: str,
    pattern: str | Pattern[str],
    error_message: str | None = None,
    flags: int = 0,
) -> str:
    """Validate string matches a regex pattern.

    Args:
        value: String to validate
        pattern: Regex pattern (string or compiled)
        error_message: Custom error message (optional)
        flags: Regex flags (default: 0)

    Returns:
        Original value if valid

    Raises:
        ValueError: If value doesn't match pattern

    Example:
        >>> validate_regex_pattern("eng", r"^[a-z]{3}$", "Must be 3 lowercase letters")
        'eng'
    """
    if isinstance(pattern, str):
        compiled_pattern = re.compile(pattern, flags)
    else:
        compiled_pattern = pattern

    if not compiled_pattern.fullmatch(value):
        if error_message:
            raise ValueError(error_message)
        else:
            raise ValueError(f"Value '{value}' does not match pattern {compiled_pattern.pattern}")

    return value


def validate_language_code_format(
    value: str,
    pattern: str | Pattern[str],
    min_length: int = 2,
    max_length: int = 10,
) -> str:
    """Validate language code format with common patterns.

    Convenience wrapper around validate_regex_pattern for language codes.

    Args:
        value: Language code to validate
        pattern: Regex pattern for language format
        min_length: Minimum code length
        max_length: Maximum code length

    Returns:
        Original value if valid

    Raises:
        ValueError: If format is invalid

    Example:
        >>> validate_language_code_format("en-US", PATTERN_IETF_BCP47)
        'en-US'
    """
    if len(value) < min_length or len(value) > max_length:
        raise ValueError(
            f"Language code '{value}' length must be between {min_length} and {max_length}"
        )

    return validate_regex_pattern(value, pattern, f"Invalid language code format: '{value}'")


# ============================================================================
# Numeric Range Validators
# ============================================================================


def validate_int_range(
    value: int,
    min_value: int | None = None,
    max_value: int | None = None,
    field_name: str = "value",
) -> int:
    """Validate integer is within specified range.

    Args:
        value: Integer to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Field name for error messages

    Returns:
        Original value if valid

    Raises:
        ValueError: If value is out of range

    Example:
        >>> validate_int_range(5, 0, 13, "psm")
        5
    """
    if min_value is not None and value < min_value:
        raise ValueError(f"Field '{field_name}' must be at least {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"Field '{field_name}' must be at most {max_value}, got {value}")

    return value


def validate_float_range(
    value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    field_name: str = "value",
) -> float:
    """Validate float is within specified range.

    Args:
        value: Float to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Field name for error messages

    Returns:
        Original value if valid

    Raises:
        ValueError: If value is out of range

    Example:
        >>> validate_float_range(0.7, 0.0, 1.0, "text_threshold")
        0.7
    """
    if min_value is not None and value < min_value:
        raise ValueError(f"Field '{field_name}' must be at least {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"Field '{field_name}' must be at most {max_value}, got {value}")

    return value


def validate_probability(value: float, field_name: str = "probability") -> float:
    """Validate value is a valid probability (0.0 to 1.0).

    Convenience wrapper for common 0.0-1.0 range validation.

    Args:
        value: Probability value to validate
        field_name: Field name for error messages

    Returns:
        Original value if valid

    Raises:
        ValueError: If value is not in [0.0, 1.0]

    Example:
        >>> validate_probability(0.7, "text_threshold")
        0.7
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Field '{field_name}' must be between 0.0 and 1.0, got {value}")

    return value


# ============================================================================
# List Validators
# ============================================================================


def validate_list_length(
    value: list[T],
    min_length: int | None = None,
    max_length: int | None = None,
    field_name: str = "list",
) -> list[T]:
    """Validate list has acceptable length.

    Args:
        value: List to validate
        min_length: Minimum number of items
        max_length: Maximum number of items
        field_name: Field name for error messages

    Returns:
        Original list if valid

    Raises:
        ValueError: If length is out of bounds

    Example:
        >>> validate_list_length(["en", "fr"], min_length=1, max_length=5)
        ['en', 'fr']
    """
    list_len = len(value)

    if min_length is not None and list_len < min_length:
        raise ValueError(
            f"Field '{field_name}' must have at least {min_length} item(s), got {list_len}"
        )

    if max_length is not None and list_len > max_length:
        raise ValueError(
            f"Field '{field_name}' must have at most {max_length} item(s), got {list_len}"
        )

    return value


def validate_whitelist(
    values: list[str],
    allowed: set[str] | frozenset[str],
    field_name: str = "value",
    suggestion_count: int = 10,
) -> list[str]:
    """Validate all items are in allowed whitelist.

    Args:
        values: List of values to validate
        allowed: Set of allowed values
        field_name: Field name for error messages
        suggestion_count: Number of suggestions to show in error

    Returns:
        Original list if all valid

    Raises:
        ValueError: If any value not in whitelist, includes suggestions

    Example:
        >>> validate_whitelist(["en", "fr"], {"en", "fr", "de"})
        ['en', 'fr']
    """
    invalid = [v for v in values if v not in allowed]

    if invalid:
        # Show sample of allowed values
        allowed_sample = sorted(allowed)[:suggestion_count]
        sample_str = ", ".join(allowed_sample)

        total_allowed = len(allowed)
        if total_allowed > suggestion_count:
            sample_str += f" (showing {suggestion_count} of {total_allowed} options)"

        raise ValueError(
            f"Invalid values for '{field_name}': {invalid}. Allowed values include: {sample_str}"
        )

    return values


# ============================================================================
# String Normalization Helpers
# ============================================================================


def normalize_lowercase(value: str | None) -> str | None:
    """Normalize string to lowercase and trim whitespace.

    Args:
        value: String to normalize (can be None)

    Returns:
        Normalized string or None if input was None

    Example:
        >>> normalize_lowercase("  ENG  ")
        'eng'
    """
    if value is None:
        return None

    return value.strip().lower()


def normalize_language_list(
    values: list[str],
    to_lowercase: bool = False,
) -> list[str]:
    """Normalize list of language codes.

    Args:
        values: List of language codes
        to_lowercase: Whether to convert to lowercase

    Returns:
        Normalized list (trimmed whitespace, optionally lowercased)

    Example:
        >>> normalize_language_list(["  EN  ", " fr "], to_lowercase=True)
        ['en', 'fr']
    """
    normalized = [v.strip() for v in values]

    if to_lowercase:
        normalized = [v.lower() for v in normalized]

    return normalized


# ============================================================================
# Composite Validators (Higher-Order Functions)
# ============================================================================


def create_split_string_validator(
    separator: str = "+",
    segment_pattern: str | Pattern[str] | None = None,
    max_segments: int | None = None,
) -> Callable[[str], list[str]]:
    """Create a validator for delimited strings (e.g., "eng+fra+deu").

    Returns a function that validates and splits strings.

    Args:
        separator: String separator (e.g., "+")
        segment_pattern: Optional regex pattern for each segment
        max_segments: Maximum number of segments

    Returns:
        Validator function that takes a string and returns list of segments

    Raises:
        ValueError: If validation fails

    Example:
        >>> validator = create_split_string_validator("+", r"^[a-z_]{3,7}$", max_segments=5)
        >>> validator("eng+fra")
        ['eng', 'fra']
    """

    def validator(value: str) -> list[str]:
        segments = value.split(separator)

        # Validate segment count
        if max_segments is not None and len(segments) > max_segments:
            raise ValueError(f"Maximum {max_segments} segments allowed, got {len(segments)}")

        # Validate each segment format if pattern provided
        if segment_pattern is not None:
            compiled_pattern = (
                re.compile(segment_pattern) if isinstance(segment_pattern, str) else segment_pattern
            )

            invalid = [s for s in segments if not compiled_pattern.fullmatch(s)]
            if invalid:
                raise ValueError(
                    f"Invalid segment format: {', '.join(invalid)}. "
                    f"Must match pattern {compiled_pattern.pattern}"
                )

        return segments

    return validator


# ============================================================================
# Common Regex Patterns (Constants)
# ============================================================================

# Language code patterns
PATTERN_IETF_BCP47 = re.compile(r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-[A-Z]{2})?$", re.IGNORECASE)
PATTERN_TESSERACT_LANG_SEGMENT = re.compile(r"^[a-z_]{3,7}$")
PATTERN_ISO_639_1 = re.compile(r"^[a-z]{2}$")  # Two-letter codes
PATTERN_ISO_639_2 = re.compile(r"^[a-z]{3}$")  # Three-letter codes

# File format patterns
PATTERN_FILE_EXTENSION = re.compile(r"^\.[a-z0-9]+$")
