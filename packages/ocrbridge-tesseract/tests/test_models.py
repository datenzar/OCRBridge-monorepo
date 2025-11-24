"""Tests for TesseractParams validation model."""

import subprocess
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from ocrbridge.engines.tesseract.models import TesseractParams, get_installed_languages


class TestTesseractParamsDefaults:
    """Test default parameter values."""

    def test_default_params(self):
        """Test that default parameters are set correctly."""
        params = TesseractParams()
        assert params.lang == "eng"
        assert params.psm == 3
        assert params.oem == 1
        assert params.dpi == 300


class TestLanguageValidation:
    """Test language parameter validation."""

    def test_single_language(self, mock_installed_languages):
        """Test single language codes."""
        params = TesseractParams(lang="eng")
        assert params.lang == "eng"

        params = TesseractParams(lang="fra")
        assert params.lang == "fra"

        params = TesseractParams(lang="deu")
        assert params.lang == "deu"

        params = TesseractParams(lang="chi_sim")
        assert params.lang == "chi_sim"

    def test_multiple_languages(self, mock_installed_languages):
        """Test multiple language combinations."""
        params = TesseractParams(lang="eng+fra")
        assert params.lang == "eng+fra"

        params = TesseractParams(lang="eng+fra+deu")
        assert params.lang == "eng+fra+deu"

        # Test maximum 5 languages
        params = TesseractParams(lang="eng+fra+deu+spa+ita")
        assert params.lang == "eng+fra+deu+spa+ita"

    def test_language_normalization(self, mock_installed_languages):
        """Test that language codes are normalized to lowercase."""
        params = TesseractParams(lang="  ENG  ")
        assert params.lang == "eng"

        params = TesseractParams(lang="ENG+FRA")
        assert params.lang == "eng+fra"

        # Test with leading/trailing whitespace
        params = TesseractParams(lang="  ENG+FRA  ")
        assert params.lang == "eng+fra"

    def test_too_many_languages(self, mock_installed_languages):
        """Test that more than 5 languages raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="eng+fra+deu+spa+ita+por")
        assert "Maximum 5 languages allowed" in str(exc_info.value)

    def test_invalid_language_format_too_short(self, mock_installed_languages):
        """Test that language codes too short are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="en")
        assert "Invalid language format" in str(
            exc_info.value
        ) or "String should match pattern" in str(exc_info.value)

    def test_invalid_language_format_too_long(self, mock_installed_languages):
        """Test that language codes too long are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="englishlang")
        assert "Invalid language format" in str(
            exc_info.value
        ) or "String should match pattern" in str(exc_info.value)

    def test_invalid_language_format_numbers(self, mock_installed_languages):
        """Test that language codes with numbers are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="eng123")
        assert "String should match pattern" in str(exc_info.value)

    def test_invalid_language_format_hyphen(self, mock_installed_languages):
        """Test that language codes with hyphens are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="eng-us")
        assert "String should match pattern" in str(exc_info.value)

    def test_language_not_installed(self, mock_installed_languages):
        """Test that uninstalled languages raise an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="zzz")
        assert "Language(s) not installed" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_mixed_installed_uninstalled(self, mock_installed_languages):
        """Test mixed installed and uninstalled languages."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="eng+zzz")
        assert "Language(s) not installed" in str(exc_info.value)
        assert "zzz" in str(exc_info.value)

    def test_language_none(self):
        """Test that None language is allowed."""
        params = TesseractParams(lang=None)
        assert params.lang is None


class TestPSMValidation:
    """Test Page Segmentation Mode parameter validation."""

    @pytest.mark.parametrize("psm_value", list(range(14)))
    def test_psm_valid_range(self, psm_value):
        """Test all valid PSM values 0-13."""
        params = TesseractParams(psm=psm_value)
        assert params.psm == psm_value

    def test_psm_below_range(self):
        """Test that PSM below 0 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(psm=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_psm_above_range(self):
        """Test that PSM above 13 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(psm=14)
        assert "less than or equal to 13" in str(exc_info.value)

    def test_psm_none(self):
        """Test that None PSM is allowed."""
        params = TesseractParams(psm=None)
        assert params.psm is None


class TestOEMValidation:
    """Test OCR Engine Mode parameter validation."""

    @pytest.mark.parametrize("oem_value", [0, 1, 2, 3])
    def test_oem_valid_range(self, oem_value):
        """Test all valid OEM values 0-3."""
        params = TesseractParams(oem=oem_value)
        assert params.oem == oem_value

    def test_oem_below_range(self):
        """Test that OEM below 0 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(oem=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_oem_above_range(self):
        """Test that OEM above 3 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(oem=4)
        assert "less than or equal to 3" in str(exc_info.value)

    def test_oem_none(self):
        """Test that None OEM is allowed."""
        params = TesseractParams(oem=None)
        assert params.oem is None


class TestDPIValidation:
    """Test DPI parameter validation."""

    @pytest.mark.parametrize("dpi_value", [70, 150, 300, 600, 1200, 2400])
    def test_dpi_valid_range(self, dpi_value):
        """Test various valid DPI values."""
        params = TesseractParams(dpi=dpi_value)
        assert params.dpi == dpi_value

    def test_dpi_minimum_boundary(self):
        """Test DPI at minimum boundary."""
        params = TesseractParams(dpi=70)
        assert params.dpi == 70

    def test_dpi_maximum_boundary(self):
        """Test DPI at maximum boundary."""
        params = TesseractParams(dpi=2400)
        assert params.dpi == 2400

    def test_dpi_below_range(self):
        """Test that DPI below 70 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(dpi=69)
        assert "greater than or equal to 70" in str(exc_info.value)

    def test_dpi_above_range(self):
        """Test that DPI above 2400 raises an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(dpi=2401)
        assert "less than or equal to 2400" in str(exc_info.value)

    def test_dpi_none(self):
        """Test that None DPI is allowed."""
        params = TesseractParams(dpi=None)
        assert params.dpi is None


class TestGetInstalledLanguages:
    """Test get_installed_languages function."""

    def test_get_installed_languages_success(self, monkeypatch):
        """Test successful language retrieval from Tesseract."""
        # Clear the cache first
        get_installed_languages.cache_clear()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "List of available languages (3):\neng\nfra\ndeu\n"

        def mock_run(*args, **kwargs):
            return mock_result

        monkeypatch.setattr(subprocess, "run", mock_run)

        langs = get_installed_languages()
        assert "eng" in langs
        assert "fra" in langs
        assert "deu" in langs

    def test_get_installed_languages_command_fails(self, monkeypatch):
        """Test fallback when tesseract command fails."""
        get_installed_languages.cache_clear()

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        def mock_run(*args, **kwargs):
            return mock_result

        monkeypatch.setattr(subprocess, "run", mock_run)

        langs = get_installed_languages()
        # Should fall back to defaults
        assert "eng" in langs
        assert "fra" in langs

    def test_get_installed_languages_not_found(self, monkeypatch):
        """Test fallback when tesseract binary not found."""
        get_installed_languages.cache_clear()

        def mock_run(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr(subprocess, "run", mock_run)

        langs = get_installed_languages()
        # Should fall back to defaults
        assert "eng" in langs

    def test_get_installed_languages_timeout(self, monkeypatch):
        """Test fallback when tesseract command times out."""
        get_installed_languages.cache_clear()

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="tesseract", timeout=5)

        monkeypatch.setattr(subprocess, "run", mock_run)

        langs = get_installed_languages()
        # Should fall back to defaults
        assert "eng" in langs

    def test_get_installed_languages_caching(self, monkeypatch):
        """Test that results are cached."""
        get_installed_languages.cache_clear()

        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "List of available languages (1):\neng\n"
            return mock_result

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Call twice
        langs1 = get_installed_languages()
        langs2 = get_installed_languages()

        assert langs1 == langs2
        # Should only call subprocess once due to caching
        assert call_count == 1


class TestCombinedParameters:
    """Test combinations of parameters."""

    def test_all_parameters_custom(self, mock_installed_languages):
        """Test creating params with all custom values."""
        params = TesseractParams(lang="eng+fra", psm=6, oem=1, dpi=600)
        assert params.lang == "eng+fra"
        assert params.psm == 6
        assert params.oem == 1
        assert params.dpi == 600

    def test_partial_parameters(self, mock_installed_languages):
        """Test creating params with some defaults."""
        params = TesseractParams(lang="deu", psm=11)
        assert params.lang == "deu"
        assert params.psm == 11
        assert params.oem == 1  # default
        assert params.dpi == 300  # default

    def test_extra_fields_forbidden(self, mock_installed_languages):
        """Test that extra fields raise an error."""
        with pytest.raises(ValidationError) as exc_info:
            TesseractParams(lang="eng", unknown_param="value")
        assert "Extra inputs are not permitted" in str(exc_info.value)
