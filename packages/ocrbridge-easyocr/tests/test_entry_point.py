"""Tests for Python entry point discovery."""

from importlib.metadata import entry_points

from ocrbridge.core import OCREngine

from ocrbridge.engines.easyocr import EasyOCREngine


class TestEntryPoint:
    """Test suite for ocrbridge.engines entry point."""

    def test_entry_point_exists(self) -> None:
        """Test that the easyocr entry point is registered."""
        # Get entry points for ocrbridge.engines group
        eps = entry_points()

        # Handle both old and new entry_points() API
        if hasattr(eps, "select"):
            # Python 3.10+ API
            engine_eps = eps.select(group="ocrbridge.engines")
        else:
            # Python 3.9 API
            engine_eps = eps.get("ocrbridge.engines", [])

        # Convert to list and check
        engine_list = list(engine_eps)
        entry_names = [ep.name for ep in engine_list]

        assert "easyocr" in entry_names, (
            f"Entry point 'easyocr' not found in ocrbridge.engines. Found: {entry_names}"
        )

    def test_entry_point_loads_correct_class(self) -> None:
        """Test that the entry point loads the EasyOCREngine class."""
        # Get entry points
        eps = entry_points()

        if hasattr(eps, "select"):
            engine_eps = eps.select(group="ocrbridge.engines")
        else:
            engine_eps = eps.get("ocrbridge.engines", [])

        # Find the easyocr entry point
        easyocr_ep = None
        for ep in engine_eps:
            if ep.name == "easyocr":
                easyocr_ep = ep
                break

        assert easyocr_ep is not None, "easyocr entry point not found"

        # Load the entry point
        engine_class = easyocr_ep.load()

        # Verify it's the correct class
        assert engine_class is EasyOCREngine

    def test_entry_point_class_is_instantiable(self) -> None:
        """Test that the entry point class can be instantiated."""
        # Get entry points
        eps = entry_points()

        if hasattr(eps, "select"):
            engine_eps = eps.select(group="ocrbridge.engines")
        else:
            engine_eps = eps.get("ocrbridge.engines", [])

        # Find and load the easyocr entry point
        easyocr_ep = None
        for ep in engine_eps:
            if ep.name == "easyocr":
                easyocr_ep = ep
                break

        assert easyocr_ep is not None, "easyocr entry point not found"

        engine_class = easyocr_ep.load()

        # Instantiate the class
        engine = engine_class()

        # Verify instance
        assert isinstance(engine, EasyOCREngine)
        assert isinstance(engine, OCREngine)

    def test_entry_point_engine_has_required_interface(self) -> None:
        """Test that the entry point engine implements the OCREngine interface."""
        # Get entry points
        eps = entry_points()

        if hasattr(eps, "select"):
            engine_eps = eps.select(group="ocrbridge.engines")
        else:
            engine_eps = eps.get("ocrbridge.engines", [])

        # Find and load the easyocr entry point
        easyocr_ep = None
        for ep in engine_eps:
            if ep.name == "easyocr":
                easyocr_ep = ep
                break

        assert easyocr_ep is not None, "easyocr entry point not found"

        engine_class = easyocr_ep.load()
        engine = engine_class()

        # Check required properties exist
        assert hasattr(engine, "name")
        assert hasattr(engine, "supported_formats")
        assert hasattr(engine, "process")

        # Check properties have correct types
        assert isinstance(engine.name, str)
        assert isinstance(engine.supported_formats, set)
        assert callable(engine.process)

        # Check values
        assert engine.name == "easyocr"
        assert len(engine.supported_formats) > 0


class TestEntryPointValue:
    """Test suite for entry point configuration values."""

    def test_entry_point_module_path(self) -> None:
        """Test that entry point points to correct module path."""
        # Get entry points
        eps = entry_points()

        if hasattr(eps, "select"):
            engine_eps = eps.select(group="ocrbridge.engines")
        else:
            engine_eps = eps.get("ocrbridge.engines", [])

        # Find the easyocr entry point
        easyocr_ep = None
        for ep in engine_eps:
            if ep.name == "easyocr":
                easyocr_ep = ep
                break

        assert easyocr_ep is not None

        # Check the entry point value
        # Format should be: "ocrbridge.engines.easyocr:EasyOCREngine"
        assert "ocrbridge.engines.easyocr" in easyocr_ep.value
        assert "EasyOCREngine" in easyocr_ep.value
