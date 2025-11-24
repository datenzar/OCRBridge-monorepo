# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the EasyOCR engine implementation for OCR Bridge - a plugin that provides deep learning-based OCR using the EasyOCR library. It's part of the larger OCR Bridge architecture which provides a unified interface for different OCR engines.

## Development Commands

### Setup
```zsh
make install          # Install dependencies with uv (includes dev extras)
```

### Testing & Quality
```zsh
make test            # Run pytest test suite
make lint            # Run ruff linter
make format          # Format code with ruff
make typecheck       # Type check with pyright
make check           # Run all checks: lint + typecheck + test
make all             # Run check + format (default target)
```

### Running Single Tests
```zsh
uv run pytest tests/test_specific.py          # Run specific test file
uv run pytest tests/test_specific.py::test_fn # Run specific test function
uv run pytest -k "test_pattern"               # Run tests matching pattern
```

### Building
```zsh
uv build             # Build distribution packages
```

## Architecture

### Entry Point System
This package uses Python entry points for automatic discovery by OCR Bridge:
- Entry point: `ocrbridge.engines` → `easyocr = "ocrbridge.engines.easyocr:EasyOCREngine"`
- Defined in `pyproject.toml` under `[project.entry-points]`
- The engine is automatically discovered when installed alongside ocrbridge-core

### Core Components

**`src/ocrbridge/engines/easyocr/engine.py`**
- `EasyOCREngine`: Main engine class implementing the `OCREngine` interface from ocrbridge-core
- GPU detection and automatic device selection via `detect_gpu_availability()` and `get_easyocr_device()`
- Handles both single images and multi-page PDFs
- PDF processing: converts pages to images via pdf2image, processes each page, merges HOCR output
- Lazy initialization: EasyOCR Reader is created on first use and cached/reused for same language configuration

**`src/ocrbridge/engines/easyocr/models.py`**
- `EasyOCRParams`: Pydantic model for engine parameters (extends `OCREngineParams` from core)
- Validates language codes against 80+ supported EasyOCR languages
- Parameters: `languages` (list, max 5), `text_threshold` (0.0-1.0), `link_threshold` (0.0-1.0)
- Language codes use EasyOCR format (e.g., "en", "ch_sim", "ja"), NOT Tesseract format

### Dependencies
- **ocrbridge-core**: Core interfaces and utilities (OCREngine, easyocr_to_hocr converter)
- **easyocr**: Deep learning OCR library (~2GB with PyTorch)
- **torch**: PyTorch for neural network models and GPU support
- **pdf2image**: Converts PDF pages to images for processing
- **Pillow**: Image handling
- **numpy**: Array operations for image data

### GPU Support
- Engine automatically detects CUDA availability via `torch.cuda.is_available()`
- Gracefully falls back to CPU if GPU unavailable
- No configuration needed - handled transparently in `_create_reader()`

## Code Quality Standards

### Commit Messages
Follow Conventional Commits format:
```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`

Examples:
- `feat(engine): add batch processing support`
- `fix: resolve GPU memory leak in multi-page PDFs`
- `docs: update language code examples`

### Python Style
- **Line length**: 100 characters (Ruff configured)
- **Python version**: 3.11+ (uses modern type hints like `list[str]`, `tuple[float, float]`)
- **Type checking**: Strict mode with pyright
- **Linting**: Ruff with rules E, F, I, N, W enabled
- Type annotations required on all public functions
- Use `cast()` for complex types from untyped libraries (easyocr, pdf2image)

### Testing
- Tests in `tests/` directory
- Pytest markers available:
  - `@pytest.mark.integration`: Tests requiring external dependencies
  - `@pytest.mark.slow`: Long-running tests
- Sample test files in `samples/`: PDFs and images for testing various scenarios
- Pythonpath configured to include `src/` for imports

## CI/CD
- GitHub Actions workflows in `.github/workflows/`:
  - `python-package.yml`: Tests on Python 3.10-3.14
  - `release.yml`: Automated releases with semantic versioning
  - `conventional-commits.yml`: Validates commit message format
- Uses `uv` package manager (version 0.9.3 in CI)
- All quality checks must pass: lint, format, typecheck, test
