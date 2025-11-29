"""Tests for validation utilities."""

import re

import pytest

from ocrbridge.core.validation import (
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

# ============================================================================
# Regex Pattern Validators
# ============================================================================


class TestValidateRegexPattern:
    """Tests for validate_regex_pattern function."""

    def test_valid_pattern_string(self):
        """Test validation with valid string pattern."""
        result = validate_regex_pattern("eng", r"^[a-z]{3}$")
        assert result == "eng"

    def test_valid_pattern_compiled(self):
        """Test validation with compiled pattern."""
        pattern = re.compile(r"^[a-z]{3}$")
        result = validate_regex_pattern("eng", pattern)
        assert result == "eng"

    def test_invalid_pattern_default_error(self):
        """Test validation with invalid pattern and default error message."""
        with pytest.raises(ValueError) as exc:
            validate_regex_pattern("ENG", r"^[a-z]{3}$")
        assert "does not match pattern" in str(exc.value)
        assert "ENG" in str(exc.value)

    def test_invalid_pattern_custom_error(self):
        """Test validation with invalid pattern and custom error message."""
        with pytest.raises(ValueError) as exc:
            validate_regex_pattern("ENG", r"^[a-z]{3}$", "Must be lowercase")
        assert "Must be lowercase" in str(exc.value)

    def test_pattern_with_flags(self):
        """Test validation with regex flags."""
        result = validate_regex_pattern("ENG", r"^[a-z]{3}$", flags=re.IGNORECASE)
        assert result == "ENG"


class TestValidateLanguageCodeFormat:
    """Tests for validate_language_code_format function."""

    def test_valid_language_code(self):
        """Test validation with valid language code."""
        result = validate_language_code_format("en-US", PATTERN_IETF_BCP47)
        assert result == "en-US"

    def test_too_short(self):
        """Test validation with language code too short."""
        with pytest.raises(ValueError) as exc:
            validate_language_code_format("a", PATTERN_IETF_BCP47, min_length=2)
        assert "length must be between" in str(exc.value)

    def test_too_long(self):
        """Test validation with language code too long."""
        with pytest.raises(ValueError) as exc:
            validate_language_code_format("toolongcode", PATTERN_IETF_BCP47, max_length=10)
        assert "length must be between" in str(exc.value)

    def test_invalid_format(self):
        """Test validation with invalid format."""
        with pytest.raises(ValueError) as exc:
            validate_language_code_format("invalid", PATTERN_IETF_BCP47)
        assert "Invalid language code format" in str(exc.value)


# ============================================================================
# Numeric Range Validators
# ============================================================================


class TestValidateIntRange:
    """Tests for validate_int_range function."""

    def test_within_bounds(self):
        """Test validation with value within bounds."""
        result = validate_int_range(5, min_value=0, max_value=10, field_name="psm")
        assert result == 5

    def test_at_min_boundary(self):
        """Test validation at minimum boundary."""
        result = validate_int_range(0, min_value=0, max_value=10)
        assert result == 0

    def test_at_max_boundary(self):
        """Test validation at maximum boundary."""
        result = validate_int_range(10, min_value=0, max_value=10)
        assert result == 10

    def test_below_min(self):
        """Test validation with value below minimum."""
        with pytest.raises(ValueError) as exc:
            validate_int_range(-1, min_value=0, field_name="psm")
        assert "must be at least 0" in str(exc.value)
        assert "psm" in str(exc.value)

    def test_above_max(self):
        """Test validation with value above maximum."""
        with pytest.raises(ValueError) as exc:
            validate_int_range(15, max_value=13, field_name="psm")
        assert "must be at most 13" in str(exc.value)
        assert "psm" in str(exc.value)

    def test_no_bounds(self):
        """Test validation with no bounds set."""
        result = validate_int_range(999)
        assert result == 999


class TestValidateFloatRange:
    """Tests for validate_float_range function."""

    def test_within_bounds(self):
        """Test validation with value within bounds."""
        result = validate_float_range(0.5, min_value=0.0, max_value=1.0)
        assert result == 0.5

    def test_at_min_boundary(self):
        """Test validation at minimum boundary."""
        result = validate_float_range(0.0, min_value=0.0, max_value=1.0)
        assert result == 0.0

    def test_at_max_boundary(self):
        """Test validation at maximum boundary."""
        result = validate_float_range(1.0, min_value=0.0, max_value=1.0)
        assert result == 1.0

    def test_below_min(self):
        """Test validation with value below minimum."""
        with pytest.raises(ValueError) as exc:
            validate_float_range(-0.1, min_value=0.0, field_name="threshold")
        assert "must be at least 0.0" in str(exc.value)
        assert "threshold" in str(exc.value)

    def test_above_max(self):
        """Test validation with value above maximum."""
        with pytest.raises(ValueError) as exc:
            validate_float_range(1.5, max_value=1.0, field_name="threshold")
        assert "must be at most 1.0" in str(exc.value)
        assert "threshold" in str(exc.value)

    def test_no_bounds(self):
        """Test validation with no bounds set."""
        result = validate_float_range(999.999)
        assert result == 999.999


class TestValidateProbability:
    """Tests for validate_probability function."""

    def test_valid_probability_middle(self):
        """Test validation with probability in middle of range."""
        result = validate_probability(0.7, "text_threshold")
        assert result == 0.7

    def test_valid_probability_zero(self):
        """Test validation with probability at 0.0."""
        result = validate_probability(0.0)
        assert result == 0.0

    def test_valid_probability_one(self):
        """Test validation with probability at 1.0."""
        result = validate_probability(1.0)
        assert result == 1.0

    def test_invalid_too_low(self):
        """Test validation with probability below 0.0."""
        with pytest.raises(ValueError) as exc:
            validate_probability(-0.1, "text_threshold")
        assert "must be between 0.0 and 1.0" in str(exc.value)
        assert "text_threshold" in str(exc.value)

    def test_invalid_too_high(self):
        """Test validation with probability above 1.0."""
        with pytest.raises(ValueError) as exc:
            validate_probability(1.5, "link_threshold")
        assert "must be between 0.0 and 1.0" in str(exc.value)
        assert "link_threshold" in str(exc.value)


# ============================================================================
# List Validators
# ============================================================================


class TestValidateListLength:
    """Tests for validate_list_length function."""

    def test_valid_length(self):
        """Test validation with valid list length."""
        result = validate_list_length(["en", "fr"], min_length=1, max_length=5)
        assert result == ["en", "fr"]

    def test_at_min_boundary(self):
        """Test validation at minimum boundary."""
        result = validate_list_length(["en"], min_length=1, max_length=5)
        assert result == ["en"]

    def test_at_max_boundary(self):
        """Test validation at maximum boundary."""
        result = validate_list_length(["a", "b", "c", "d", "e"], min_length=1, max_length=5)
        assert result == ["a", "b", "c", "d", "e"]

    def test_too_short(self):
        """Test validation with list too short."""
        with pytest.raises(ValueError) as exc:
            validate_list_length([], min_length=1, field_name="languages")
        assert "must have at least 1 item(s)" in str(exc.value)
        assert "languages" in str(exc.value)

    def test_too_long(self):
        """Test validation with list too long."""
        with pytest.raises(ValueError) as exc:
            validate_list_length(
                ["a", "b", "c", "d", "e", "f"], max_length=5, field_name="languages"
            )
        assert "must have at most 5 item(s)" in str(exc.value)
        assert "languages" in str(exc.value)

    def test_no_constraints(self):
        """Test validation with no constraints."""
        result = validate_list_length(["a"] * 100)
        assert len(result) == 100


class TestValidateWhitelist:
    """Tests for validate_whitelist function."""

    def test_all_valid(self):
        """Test validation with all values in whitelist."""
        allowed = {"en", "fr", "de", "es", "it"}
        result = validate_whitelist(["en", "fr"], allowed)
        assert result == ["en", "fr"]

    def test_with_invalid_values(self):
        """Test validation with invalid values."""
        allowed = {"en", "fr", "de"}
        with pytest.raises(ValueError) as exc:
            validate_whitelist(["en", "xx"], allowed, field_name="languages")
        assert "Invalid values for 'languages'" in str(exc.value)
        assert "['xx']" in str(exc.value)

    def test_error_includes_suggestions(self):
        """Test that error message includes suggestions."""
        allowed = {"en", "fr", "de", "es", "it", "pt", "ru", "ar", "zh", "ja", "ko"}
        with pytest.raises(ValueError) as exc:
            validate_whitelist(["xx"], allowed, suggestion_count=5)
        assert "Allowed values include:" in str(exc.value)
        # Should show first 5 in sorted order
        error_msg = str(exc.value)
        assert any(lang in error_msg for lang in ["ar", "de", "en", "es", "fr"])

    def test_suggestion_count_limit(self):
        """Test that suggestion count is respected."""
        allowed = {f"lang{i}" for i in range(100)}
        with pytest.raises(ValueError) as exc:
            validate_whitelist(["invalid"], allowed, suggestion_count=3)
        assert "showing 3 of 100 options" in str(exc.value)

    def test_empty_list(self):
        """Test validation with empty list."""
        allowed = {"en", "fr"}
        result = validate_whitelist([], allowed)
        assert result == []


# ============================================================================
# String Normalization Helpers
# ============================================================================


class TestNormalizeLowercase:
    """Tests for normalize_lowercase function."""

    def test_normalize_string(self):
        """Test normalization of uppercase string."""
        result = normalize_lowercase("ENG")
        assert result == "eng"

    def test_with_whitespace(self):
        """Test normalization with whitespace."""
        result = normalize_lowercase("  ENG  ")
        assert result == "eng"

    def test_none_value(self):
        """Test normalization with None value."""
        result = normalize_lowercase(None)
        assert result is None

    def test_already_normalized(self):
        """Test normalization of already normalized string."""
        result = normalize_lowercase("eng")
        assert result == "eng"

    def test_mixed_case(self):
        """Test normalization of mixed case string."""
        result = normalize_lowercase("  En-US  ")
        assert result == "en-us"


class TestNormalizeLanguageList:
    """Tests for normalize_language_list function."""

    def test_normalize_whitespace_only(self):
        """Test normalization with whitespace trimming only."""
        result = normalize_language_list(["  en  ", " fr "])
        assert result == ["en", "fr"]

    def test_normalize_with_lowercase(self):
        """Test normalization with lowercase conversion."""
        result = normalize_language_list(["  EN  ", " FR "], to_lowercase=True)
        assert result == ["en", "fr"]

    def test_empty_list(self):
        """Test normalization of empty list."""
        result = normalize_language_list([])
        assert result == []

    def test_already_normalized(self):
        """Test normalization of already normalized list."""
        result = normalize_language_list(["en", "fr"])
        assert result == ["en", "fr"]


# ============================================================================
# Composite Validators
# ============================================================================


class TestCreateSplitStringValidator:
    """Tests for create_split_string_validator function."""

    def test_basic_split(self):
        """Test basic string splitting."""
        validator = create_split_string_validator("+")
        result = validator("eng+fra")
        assert result == ["eng", "fra"]

    def test_custom_separator(self):
        """Test with custom separator."""
        validator = create_split_string_validator(",")
        result = validator("eng,fra,deu")
        assert result == ["eng", "fra", "deu"]

    def test_max_segments_valid(self):
        """Test max segments validation with valid count."""
        validator = create_split_string_validator("+", max_segments=3)
        result = validator("eng+fra+deu")
        assert result == ["eng", "fra", "deu"]

    def test_max_segments_exceeded(self):
        """Test max segments validation with too many segments."""
        validator = create_split_string_validator("+", max_segments=2)
        with pytest.raises(ValueError) as exc:
            validator("eng+fra+deu")
        assert "Maximum 2 segments allowed" in str(exc.value)

    def test_segment_pattern_valid(self):
        """Test segment pattern validation with valid segments."""
        validator = create_split_string_validator("+", segment_pattern=r"^[a-z]{3}$")
        result = validator("eng+fra")
        assert result == ["eng", "fra"]

    def test_segment_pattern_invalid(self):
        """Test segment pattern validation with invalid segments."""
        validator = create_split_string_validator("+", segment_pattern=r"^[a-z]{3}$")
        with pytest.raises(ValueError) as exc:
            validator("eng+FR")
        assert "Invalid segment format" in str(exc.value)
        assert "FR" in str(exc.value)

    def test_combined_constraints(self):
        """Test validator with both max segments and pattern."""
        validator = create_split_string_validator(
            "+", segment_pattern=r"^[a-z_]{3,7}$", max_segments=5
        )
        result = validator("eng+fra+deu")
        assert result == ["eng", "fra", "deu"]

    def test_combined_constraints_invalid(self):
        """Test validator with combined constraints failing."""
        validator = create_split_string_validator(
            "+", segment_pattern=r"^[a-z_]{3,7}$", max_segments=2
        )
        with pytest.raises(ValueError) as exc:
            validator("eng+fra+deu")
        assert "Maximum 2 segments allowed" in str(exc.value)

    def test_compiled_pattern(self):
        """Test validator with compiled regex pattern."""
        pattern = re.compile(r"^[a-z]{3}$")
        validator = create_split_string_validator("+", segment_pattern=pattern)
        result = validator("eng+fra")
        assert result == ["eng", "fra"]


# ============================================================================
# Pattern Constants
# ============================================================================


class TestPatternIETFBCP47:
    """Tests for PATTERN_IETF_BCP47 constant."""

    def test_valid_codes(self):
        """Test IETF BCP 47 pattern with valid language codes."""
        valid_codes = [
            "en",
            "fr",
            "en-US",
            "fr-FR",
            "zh-Hans",
            "zh-Hant",
            "en-Latn-US",
            "zh-Hans-CN",
        ]
        for code in valid_codes:
            assert PATTERN_IETF_BCP47.fullmatch(code), f"Failed for {code}"

    def test_invalid_codes(self):
        """Test IETF BCP 47 pattern with invalid codes."""
        invalid_codes = [
            "e",  # Too short
            "english",  # Too long base
            "en_US",  # Wrong separator
            "123",  # Numbers
            "en-",  # Incomplete
        ]
        for code in invalid_codes:
            assert not PATTERN_IETF_BCP47.fullmatch(code), f"Should fail for {code}"


class TestPatternTesseractLangSegment:
    """Tests for PATTERN_TESSERACT_LANG_SEGMENT constant."""

    def test_valid_segments(self):
        """Test Tesseract language segment pattern with valid segments."""
        valid_segments = ["eng", "fra", "deu", "chi_sim", "chi_tra"]
        for segment in valid_segments:
            assert PATTERN_TESSERACT_LANG_SEGMENT.fullmatch(segment)

    def test_invalid_segments(self):
        """Test Tesseract language segment pattern with invalid segments."""
        invalid_segments = [
            "en",  # Too short
            "englishlang",  # Too long (8 chars)
            "ENG",  # Uppercase
            "en-US",  # Hyphen not allowed
            "123",  # Numbers
        ]
        for segment in invalid_segments:
            assert not PATTERN_TESSERACT_LANG_SEGMENT.fullmatch(segment)


class TestPatternISO639:
    """Tests for ISO 639 pattern constants."""

    def test_iso_639_1_valid(self):
        """Test ISO 639-1 pattern with valid two-letter codes."""
        valid_codes = ["en", "fr", "de", "es", "it"]
        for code in valid_codes:
            assert PATTERN_ISO_639_1.fullmatch(code)

    def test_iso_639_1_invalid(self):
        """Test ISO 639-1 pattern with invalid codes."""
        invalid_codes = ["e", "eng", "EN", "123"]
        for code in invalid_codes:
            assert not PATTERN_ISO_639_1.fullmatch(code)

    def test_iso_639_2_valid(self):
        """Test ISO 639-2 pattern with valid three-letter codes."""
        valid_codes = ["eng", "fra", "deu", "spa", "ita"]
        for code in valid_codes:
            assert PATTERN_ISO_639_2.fullmatch(code)

    def test_iso_639_2_invalid(self):
        """Test ISO 639-2 pattern with invalid codes."""
        invalid_codes = ["en", "english", "ENG", "123"]
        for code in invalid_codes:
            assert not PATTERN_ISO_639_2.fullmatch(code)


class TestPatternFileExtension:
    """Tests for PATTERN_FILE_EXTENSION constant."""

    def test_valid_extensions(self):
        """Test file extension pattern with valid extensions."""
        valid_extensions = [".jpg", ".png", ".pdf", ".txt", ".py"]
        for ext in valid_extensions:
            assert PATTERN_FILE_EXTENSION.fullmatch(ext)

    def test_invalid_extensions(self):
        """Test file extension pattern with invalid extensions."""
        invalid_extensions = [
            "jpg",  # Missing dot
            ".JPG",  # Uppercase
            ".jpg.png",  # Multiple dots
            ".",  # Just dot
        ]
        for ext in invalid_extensions:
            assert not PATTERN_FILE_EXTENSION.fullmatch(ext)
