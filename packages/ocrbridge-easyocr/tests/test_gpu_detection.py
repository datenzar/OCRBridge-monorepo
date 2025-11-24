"""Tests for GPU detection helper functions."""

from typing import Any

from ocrbridge.engines.easyocr.engine import detect_gpu_availability, get_easyocr_device


class TestDetectGPUAvailability:
    """Test suite for detect_gpu_availability function."""

    def test_cuda_available(self, mocker: Any) -> None:
        """Test detect_gpu_availability returns True when CUDA is available."""
        # Mock torch.cuda.is_available() to return True
        mock_torch = mocker.MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        # Clear any existing torch import
        import sys

        if "torch" in sys.modules:
            del sys.modules["torch"]

        # Re-mock torch after clearing
        mock_torch = mocker.MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        result = detect_gpu_availability()
        assert result is True

    def test_cuda_unavailable(self, mocker: Any) -> None:
        """Test detect_gpu_availability returns False when CUDA is unavailable."""
        mock_torch = mocker.MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        result = detect_gpu_availability()
        assert result is False

    def test_torch_not_installed(self, mocker: Any) -> None:
        """Test detect_gpu_availability returns False when torch not installed."""

        # Mock ImportError when trying to import torch
        def raise_import_error(*args: Any, **kwargs: Any) -> None:
            raise ImportError("No module named 'torch'")

        mocker.patch("builtins.__import__", side_effect=raise_import_error)

        result = detect_gpu_availability()
        assert result is False

    def test_torch_import_exception(self, mocker: Any) -> None:
        """Test detect_gpu_availability returns False on unexpected exception."""

        # Mock an unexpected exception during torch import
        def raise_exception(*args: Any, **kwargs: Any) -> None:
            if args[0] == "torch":
                raise RuntimeError("Unexpected error")
            return mocker.DEFAULT

        mocker.patch("builtins.__import__", side_effect=raise_exception)

        result = detect_gpu_availability()
        assert result is False


class TestGetEasyOCRDevice:
    """Test suite for get_easyocr_device function."""

    def test_returns_gpu_when_cuda_available(self, mocker: Any) -> None:
        """Test get_easyocr_device returns GPU device when CUDA is available."""
        # Mock detect_gpu_availability to return True
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.detect_gpu_availability",
            return_value=True,
        )

        # Mock torch.cuda.current_device()
        mock_torch = mocker.MagicMock()
        mock_torch.cuda.current_device.return_value = 0
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        use_gpu, device_name = get_easyocr_device()

        assert use_gpu is True
        assert device_name == "cuda:0"

    def test_returns_gpu_with_specific_device(self, mocker: Any) -> None:
        """Test get_easyocr_device returns correct device ID."""
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.detect_gpu_availability",
            return_value=True,
        )

        # Mock torch.cuda.current_device() to return device 1
        mock_torch = mocker.MagicMock()
        mock_torch.cuda.current_device.return_value = 1
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        use_gpu, device_name = get_easyocr_device()

        assert use_gpu is True
        assert device_name == "cuda:1"

    def test_returns_cpu_when_cuda_unavailable(self, mocker: Any) -> None:
        """Test get_easyocr_device returns CPU when CUDA is unavailable."""
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.detect_gpu_availability",
            return_value=False,
        )

        use_gpu, device_name = get_easyocr_device()

        assert use_gpu is False
        assert device_name == "cpu"

    def test_returns_cpu_when_torch_not_available(self, mocker: Any) -> None:
        """Test get_easyocr_device returns CPU when torch is not installed."""
        # Mock detect_gpu_availability to return False (torch not available)
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.detect_gpu_availability",
            return_value=False,
        )

        use_gpu, device_name = get_easyocr_device()

        assert use_gpu is False
        assert device_name == "cpu"

    def test_return_types(self, mocker: Any) -> None:
        """Test get_easyocr_device returns correct types."""
        mocker.patch(
            "ocrbridge.engines.easyocr.engine.detect_gpu_availability",
            return_value=False,
        )

        result = get_easyocr_device()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
