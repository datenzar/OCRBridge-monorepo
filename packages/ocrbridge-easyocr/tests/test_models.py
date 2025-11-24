"""Tests for EasyOCR parameter models."""

import pytest
from pydantic import ValidationError

from ocrbridge.engines.easyocr.models import EASYOCR_SUPPORTED_LANGUAGES, EasyOCRParams


class TestEasyOCRParams:
    """Test suite for EasyOCRParams validation."""

    def test_default_params(self) -> None:
        """Test EasyOCRParams with default values."""
        params = EasyOCRParams()
        assert params.languages == ["en"]
        assert params.text_threshold == 0.7
        assert params.link_threshold == 0.7

    def test_valid_single_language(self) -> None:
        """Test EasyOCRParams with a single valid language."""
        params = EasyOCRParams(languages=["de"])
        assert params.languages == ["de"]

    def test_valid_multiple_languages(self) -> None:
        """Test EasyOCRParams with multiple valid languages."""
        params = EasyOCRParams(languages=["en", "de", "fr"])
        assert params.languages == ["en", "de", "fr"]

    def test_valid_max_languages(self) -> None:
        """Test EasyOCRParams with maximum 5 languages."""
        params = EasyOCRParams(languages=["en", "de", "fr", "es", "it"])
        assert len(params.languages) == 5

    def test_valid_asian_languages(self) -> None:
        """Test EasyOCRParams with Asian language codes."""
        params = EasyOCRParams(languages=["ch_sim", "ja", "ko"])
        assert params.languages == ["ch_sim", "ja", "ko"]

    def test_invalid_language_code(self) -> None:
        """Test EasyOCRParams rejects invalid language codes."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(languages=["eng"])  # Tesseract format, not EasyOCR

        error = exc_info.value.errors()[0]
        assert "Unsupported EasyOCR language codes" in error["msg"]
        assert "eng" in error["msg"]

    def test_invalid_multiple_language_codes(self) -> None:
        """Test EasyOCRParams rejects multiple invalid language codes."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(languages=["eng", "chi_sim", "invalid"])

        error = exc_info.value.errors()[0]
        assert "Unsupported EasyOCR language codes" in error["msg"]

    def test_empty_languages_list(self) -> None:
        """Test EasyOCRParams rejects empty language list."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(languages=[])

        # Should fail on min_length constraint
        errors = exc_info.value.errors()
        assert any("at least 1" in err["msg"].lower() for err in errors)

    def test_too_many_languages(self) -> None:
        """Test EasyOCRParams rejects more than 5 languages."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(languages=["en", "de", "fr", "es", "it", "pt"])

        # Should fail on max_length constraint
        errors = exc_info.value.errors()
        assert any("at most 5" in err["msg"].lower() for err in errors)

    def test_valid_text_threshold_range(self) -> None:
        """Test EasyOCRParams accepts valid text threshold values."""
        params_min = EasyOCRParams(text_threshold=0.0)
        assert params_min.text_threshold == 0.0

        params_mid = EasyOCRParams(text_threshold=0.5)
        assert params_mid.text_threshold == 0.5

        params_max = EasyOCRParams(text_threshold=1.0)
        assert params_max.text_threshold == 1.0

    def test_invalid_text_threshold_below_range(self) -> None:
        """Test EasyOCRParams rejects text threshold below 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(text_threshold=-0.1)

        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in err["msg"].lower() for err in errors)

    def test_invalid_text_threshold_above_range(self) -> None:
        """Test EasyOCRParams rejects text threshold above 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(text_threshold=1.1)

        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in err["msg"].lower() for err in errors)

    def test_valid_link_threshold_range(self) -> None:
        """Test EasyOCRParams accepts valid link threshold values."""
        params_min = EasyOCRParams(link_threshold=0.0)
        assert params_min.link_threshold == 0.0

        params_mid = EasyOCRParams(link_threshold=0.5)
        assert params_mid.link_threshold == 0.5

        params_max = EasyOCRParams(link_threshold=1.0)
        assert params_max.link_threshold == 1.0

    def test_invalid_link_threshold_below_range(self) -> None:
        """Test EasyOCRParams rejects link threshold below 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(link_threshold=-0.1)

        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in err["msg"].lower() for err in errors)

    def test_invalid_link_threshold_above_range(self) -> None:
        """Test EasyOCRParams rejects link threshold above 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            EasyOCRParams(link_threshold=1.1)

        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in err["msg"].lower() for err in errors)

    def test_custom_params(self) -> None:
        """Test EasyOCRParams with all custom values."""
        params = EasyOCRParams(
            languages=["en", "de"],
            text_threshold=0.8,
            link_threshold=0.6,
        )
        assert params.languages == ["en", "de"]
        assert params.text_threshold == 0.8
        assert params.link_threshold == 0.6

    def test_model_dump(self) -> None:
        """Test EasyOCRParams can be serialized to dict."""
        params = EasyOCRParams(languages=["en", "ja"], text_threshold=0.9)
        data = params.model_dump()

        assert isinstance(data, dict)
        assert data["languages"] == ["en", "ja"]
        assert data["text_threshold"] == 0.9
        assert data["link_threshold"] == 0.7

    def test_model_fields_have_descriptions(self) -> None:
        """Test that all fields have descriptions."""
        schema = EasyOCRParams.model_json_schema()

        assert "languages" in schema["properties"]
        assert "description" in schema["properties"]["languages"]
        assert "text_threshold" in schema["properties"]
        assert "description" in schema["properties"]["text_threshold"]
        assert "link_threshold" in schema["properties"]
        assert "description" in schema["properties"]["link_threshold"]


class TestEasyOCRSupportedLanguages:
    """Test suite for EASYOCR_SUPPORTED_LANGUAGES constant."""

    def test_supported_languages_is_set(self) -> None:
        """Test EASYOCR_SUPPORTED_LANGUAGES is a set."""
        assert isinstance(EASYOCR_SUPPORTED_LANGUAGES, set)

    def test_supported_languages_not_empty(self) -> None:
        """Test EASYOCR_SUPPORTED_LANGUAGES contains languages."""
        assert len(EASYOCR_SUPPORTED_LANGUAGES) > 0

    def test_common_languages_supported(self) -> None:
        """Test common languages are in the supported set."""
        common_langs = ["en", "de", "fr", "es", "it", "ch_sim", "ja", "ko"]
        for lang in common_langs:
            assert lang in EASYOCR_SUPPORTED_LANGUAGES

    def test_language_codes_are_strings(self) -> None:
        """Test all language codes are strings."""
        for lang in EASYOCR_SUPPORTED_LANGUAGES:
            assert isinstance(lang, str)

    def test_language_codes_lowercase(self) -> None:
        """Test all language codes are lowercase or contain underscore."""
        for lang in EASYOCR_SUPPORTED_LANGUAGES:
            # EasyOCR uses lowercase with underscores (e.g., "ch_sim")
            assert lang.islower() or "_" in lang
