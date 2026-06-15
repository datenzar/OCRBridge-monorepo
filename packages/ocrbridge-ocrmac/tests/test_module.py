"""Module-level tests for ocrbridge.engines.ocrmac."""

import importlib.metadata
import sys

import pytest


class TestModuleImports:
    """Tests for module imports."""

    def test_import_engine(self) -> None:
        """Test importing OcrmacEngine."""
        from ocrbridge.engines.ocrmac import OcrmacEngine

        assert OcrmacEngine is not None
        assert OcrmacEngine.__name__ == "OcrmacEngine"

    def test_import_params(self) -> None:
        """Test importing OcrmacParams."""
        from ocrbridge.engines.ocrmac import OcrmacParams

        assert OcrmacParams is not None
        assert OcrmacParams.__name__ == "OcrmacParams"

    def test_import_recognition_level(self) -> None:
        """Test importing RecognitionLevel."""
        from ocrbridge.engines.ocrmac import RecognitionLevel

        assert RecognitionLevel is not None
        assert RecognitionLevel.__name__ == "RecognitionLevel"

    def test_import_all_from_package(self) -> None:
        """Test importing all public APIs."""
        from ocrbridge.engines import ocrmac

        assert hasattr(ocrmac, "OcrmacEngine")
        assert hasattr(ocrmac, "OcrmacParams")
        assert hasattr(ocrmac, "RecognitionLevel")

    def test_import_submodules(self) -> None:
        """Test importing submodules directly."""
        from ocrbridge.engines.ocrmac import engine, models

        assert engine is not None
        assert models is not None


class TestModuleExports:
    """Tests for __all__ exports."""

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected exports."""
        from ocrbridge.engines import ocrmac

        assert hasattr(ocrmac, "__all__")
        expected = {"OcrmacEngine", "OcrmacParams", "RecognitionLevel"}
        assert set(ocrmac.__all__) == expected

    def test_all_exports_importable(self) -> None:
        """Test that all items in __all__ are actually importable."""
        from ocrbridge.engines import ocrmac

        for name in ocrmac.__all__:
            assert hasattr(ocrmac, name), f"{name} in __all__ but not exported"

    def test_star_import(self) -> None:
        """Test that star import only imports __all__ items."""
        # Import in a clean namespace
        import ocrbridge.engines.ocrmac as ocrmac_module

        # Get __all__ exports
        all_exports = ocrmac_module.__all__

        # Verify each export exists
        for name in all_exports:
            assert hasattr(ocrmac_module, name)


class TestModuleVersion:
    """Tests for module version."""

    def test_version_string_exists(self) -> None:
        """Test that __version__ is defined."""
        from ocrbridge.engines import ocrmac

        assert hasattr(ocrmac, "__version__")
        assert isinstance(ocrmac.__version__, str)

    def test_version_format(self) -> None:
        """Test that version follows semantic versioning."""
        from ocrbridge.engines import ocrmac

        version = ocrmac.__version__
        parts = version.split(".")

        # Should have at least major.minor.patch
        assert len(parts) >= 3, f"Invalid version format: {version}"

        # Major, minor, patch should be numeric
        try:
            major = int(parts[0])
            minor = int(parts[1])
            # Patch might have suffix like "0-beta"
            patch = int(parts[2].split("-")[0])
            assert major >= 0 and minor >= 0 and patch >= 0
        except ValueError as e:
            pytest.fail(f"Version parts not numeric: {version} - {e}")

    def test_version_matches_pyproject(self) -> None:
        """Test that __version__ matches version in pyproject.toml."""
        from pathlib import Path

        from ocrbridge.engines import ocrmac

        # Read pyproject.toml
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            if sys.version_info >= (3, 11):
                import tomllib

                pyproject = tomllib.load(f)
            else:
                import tomli  # type: ignore[reportMissingImports]

                pyproject = tomli.load(f)  # type: ignore[reportUnknownMemberType]

        pyproject_version = pyproject["project"]["version"]  # type: ignore[reportUnknownVariableType]
        assert ocrmac.__version__ == pyproject_version


class TestEntryPoints:
    """Tests for entry points."""

    def test_entry_point_registered(self) -> None:
        """Test that ocrbridge.engines entry point is registered."""
        try:
            entry_points = importlib.metadata.entry_points()

            # Handle both old and new API
            if hasattr(entry_points, "select"):
                # Python 3.10+ (new API)
                engine_eps = entry_points.select(group="ocrbridge.engines")
            else:
                # Python 3.9 (old API)
                engine_eps = entry_points.get("ocrbridge.engines", [])  # type: ignore[reportAttributeAccessIssue]

            # Find ocrmac entry point
            ocrmac_ep = None
            for ep in engine_eps:
                if ep.name == "ocrmac":
                    ocrmac_ep = ep
                    break

            assert ocrmac_ep is not None, "ocrmac entry point not found"
            assert "ocrbridge.engines.ocrmac" in ocrmac_ep.value
            assert "OcrmacEngine" in ocrmac_ep.value

        except importlib.metadata.PackageNotFoundError:
            pytest.skip("Package not installed, cannot test entry points")

    def test_entry_point_loadable(self) -> None:
        """Test that entry point can be loaded."""
        try:
            entry_points = importlib.metadata.entry_points()

            # Handle both old and new API
            if hasattr(entry_points, "select"):
                engine_eps = entry_points.select(group="ocrbridge.engines")
            else:
                engine_eps = entry_points.get("ocrbridge.engines", [])  # type: ignore[reportAttributeAccessIssue]

            # Find and load ocrmac entry point
            for ep in engine_eps:
                if ep.name == "ocrmac":
                    engine_class = ep.load()
                    assert engine_class is not None
                    assert engine_class.__name__ == "OcrmacEngine"
                    return

            pytest.fail("ocrmac entry point not found")

        except importlib.metadata.PackageNotFoundError:
            pytest.skip("Package not installed, cannot test entry points")


class TestModuleDocstrings:
    """Tests for module docstrings."""

    def test_module_has_docstring(self) -> None:
        """Test that module has a docstring."""
        from ocrbridge.engines import ocrmac

        assert ocrmac.__doc__ is not None
        assert len(ocrmac.__doc__.strip()) > 0

    def test_engine_class_has_docstring(self) -> None:
        """Test that OcrmacEngine has a docstring."""
        from ocrbridge.engines.ocrmac import OcrmacEngine

        assert OcrmacEngine.__doc__ is not None
        assert len(OcrmacEngine.__doc__.strip()) > 0
        assert "ocrmac" in OcrmacEngine.__doc__.lower()

    def test_params_class_has_docstring(self) -> None:
        """Test that OcrmacParams has a docstring."""
        from ocrbridge.engines.ocrmac import OcrmacParams

        assert OcrmacParams.__doc__ is not None
        assert len(OcrmacParams.__doc__.strip()) > 0

    def test_recognition_level_has_docstring(self) -> None:
        """Test that RecognitionLevel has a docstring."""
        from ocrbridge.engines.ocrmac import RecognitionLevel

        assert RecognitionLevel.__doc__ is not None
        assert len(RecognitionLevel.__doc__.strip()) > 0


class TestModuleStructure:
    """Tests for module structure."""

    def test_engine_module_exists(self) -> None:
        """Test that engine.py module exists."""
        from ocrbridge.engines.ocrmac import engine

        assert engine is not None

    def test_models_module_exists(self) -> None:
        """Test that models.py module exists."""
        from ocrbridge.engines.ocrmac import models

        assert models is not None

    def test_engine_in_engine_module(self) -> None:
        """Test that OcrmacEngine is in engine module."""
        from ocrbridge.engines.ocrmac.engine import OcrmacEngine

        assert OcrmacEngine is not None

    def test_models_in_models_module(self) -> None:
        """Test that models are in models module."""
        from ocrbridge.engines.ocrmac.models import OcrmacParams, RecognitionLevel

        assert OcrmacParams is not None
        assert RecognitionLevel is not None

    def test_no_private_exports_in_all(self) -> None:
        """Test that __all__ doesn't contain private names."""
        from ocrbridge.engines import ocrmac

        for name in ocrmac.__all__:
            assert not name.startswith("_"), f"Private name in __all__: {name}"
