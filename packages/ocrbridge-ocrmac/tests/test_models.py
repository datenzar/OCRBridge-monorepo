"""Unit tests for ocrmac models."""

import pytest
from pydantic import ValidationError

from ocrbridge.engines.ocrmac.models import OcrmacParams, RecognitionLevel


class TestRecognitionLevel:
    """Tests for RecognitionLevel enum."""

    def test_recognition_level_values(self) -> None:
        """Test that all recognition levels have correct values."""
        assert RecognitionLevel.FAST.value == "fast"
        assert RecognitionLevel.BALANCED.value == "balanced"
        assert RecognitionLevel.ACCURATE.value == "accurate"
        assert RecognitionLevel.LIVETEXT.value == "livetext"

    def test_recognition_level_is_string_enum(self) -> None:
        """Test that RecognitionLevel is a string enum."""
        assert isinstance(RecognitionLevel.FAST, str)
        assert isinstance(RecognitionLevel.BALANCED, str)

    def test_recognition_level_count(self) -> None:
        """Test that we have exactly 4 recognition levels."""
        assert len(RecognitionLevel) == 4


class TestOcrmacParams:
    """Tests for OcrmacParams model."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        params = OcrmacParams()
        assert params.languages is None
        assert params.recognition_level == RecognitionLevel.BALANCED

    def test_explicit_values(self) -> None:
        """Test setting explicit values."""
        params = OcrmacParams(
            languages=["en-US", "fr-FR"], recognition_level=RecognitionLevel.ACCURATE
        )
        assert params.languages == ["en-US", "fr-FR"]
        assert params.recognition_level == RecognitionLevel.ACCURATE

    def test_recognition_level_from_string(self) -> None:
        """Test that recognition level can be set from string value."""
        params = OcrmacParams(recognition_level="fast")  # type: ignore[reportArgumentType]
        assert params.recognition_level == RecognitionLevel.FAST

    # Language validation tests

    def test_valid_language_codes(self) -> None:
        """Test valid IETF BCP 47 language codes."""
        valid_codes = [
            ["en"],
            ["en-US"],
            ["fr-FR"],
            ["zh-Hans"],
            ["zh-Hans-CN"],
            ["de-DE"],
            ["ja-JP"],
            ["pt-BR"],
        ]

        for codes in valid_codes:
            params = OcrmacParams(languages=codes)
            assert params.languages == codes

    def test_multiple_languages(self) -> None:
        """Test setting multiple languages."""
        params = OcrmacParams(languages=["en-US", "fr-FR", "de-DE"])
        assert params.languages == ["en-US", "fr-FR", "de-DE"]

    def test_max_five_languages(self) -> None:
        """Test that exactly 5 languages is allowed."""
        params = OcrmacParams(languages=["en-US", "fr-FR", "de-DE", "es-ES", "it-IT"])
        assert len(params.languages) == 5  # type: ignore[reportOptionalMemberAccess]

    def test_too_many_languages(self) -> None:
        """Test that more than 5 languages raises error."""
        with pytest.raises(ValidationError) as exc_info:
            OcrmacParams(languages=["en-US", "fr-FR", "de-DE", "es-ES", "it-IT", "pt-BR"])

        errors = exc_info.value.errors()
        # Pydantic validates max_length constraint
        assert any(e["type"] == "too_long" for e in errors)

    def test_invalid_language_code_format(self) -> None:
        """Test that invalid language code format raises error."""
        invalid_codes = [
            ["english"],  # Not BCP 47
            ["en_US"],  # Underscore instead of hyphen
            ["e"],  # Too short
            ["engl"],  # Too long for language code
            ["en-usa"],  # Region too long
            ["123"],  # Numbers
            [""],  # Empty string
        ]

        for codes in invalid_codes:
            with pytest.raises(ValidationError) as exc_info:
                OcrmacParams(languages=codes)

            # Should raise a value_error from our custom validator
            error_str = str(exc_info.value)
            assert "Invalid IETF BCP 47 language code" in error_str or "value_error" in error_str

    def test_empty_language_list(self) -> None:
        """Test that empty language list raises error."""
        with pytest.raises(ValidationError):
            OcrmacParams(languages=[])

    def test_none_languages(self) -> None:
        """Test that None is valid for languages."""
        params = OcrmacParams(languages=None)
        assert params.languages is None

    def test_case_insensitive_validation(self) -> None:
        """Test that language validation is case-insensitive."""
        # BCP 47 is case-insensitive but has conventions
        params = OcrmacParams(languages=["EN-us"])  # Mixed case
        assert params.languages == ["EN-us"]  # Preserves input case

    # Recognition level tests

    def test_all_recognition_levels(self) -> None:
        """Test setting all recognition levels."""
        for level in RecognitionLevel:
            params = OcrmacParams(recognition_level=level)
            assert params.recognition_level == level

    def test_invalid_recognition_level(self) -> None:
        """Test that invalid recognition level raises error."""
        with pytest.raises(ValidationError):
            OcrmacParams(recognition_level="invalid")  # type: ignore[reportArgumentType]

    # Serialization tests

    def test_model_dump(self) -> None:
        """Test model serialization."""
        params = OcrmacParams(languages=["en-US"], recognition_level=RecognitionLevel.FAST)
        dumped = params.model_dump()

        assert dumped["languages"] == ["en-US"]
        assert dumped["recognition_level"] == "fast"

    def test_model_dump_json(self) -> None:
        """Test JSON serialization."""
        params = OcrmacParams(languages=["en-US"], recognition_level=RecognitionLevel.ACCURATE)
        json_str = params.model_dump_json()

        assert "en-US" in json_str
        assert "accurate" in json_str

    def test_model_validate(self) -> None:
        """Test model validation from dict."""
        data = {"languages": ["fr-FR"], "recognition_level": "balanced"}
        params = OcrmacParams.model_validate(data)

        assert params.languages == ["fr-FR"]
        assert params.recognition_level == RecognitionLevel.BALANCED

    # Edge cases

    def test_languages_with_script_and_region(self) -> None:
        """Test language codes with both script and region."""
        params = OcrmacParams(languages=["zh-Hans-CN", "zh-Hant-TW"])
        assert params.languages == ["zh-Hans-CN", "zh-Hant-TW"]

    def test_languages_with_only_script(self) -> None:
        """Test language codes with only script."""
        params = OcrmacParams(languages=["zh-Hans", "zh-Hant"])
        assert params.languages == ["zh-Hans", "zh-Hant"]

    def test_three_letter_language_codes(self) -> None:
        """Test three-letter ISO 639-2 language codes."""
        params = OcrmacParams(languages=["eng", "fra", "deu"])
        assert params.languages == ["eng", "fra", "deu"]
