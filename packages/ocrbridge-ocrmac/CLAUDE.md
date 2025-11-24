# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `ocrbridge-ocrmac`, an OCR engine for the OCR Bridge architecture that uses Apple's Vision framework. It is a **macOS-only** package that integrates with the broader OCR Bridge plugin ecosystem via entry points.

**Key constraint**: All code must run on macOS (Darwin platform). The engine performs platform validation at runtime.

## Architecture

### Entry Point System

The engine registers itself with OCR Bridge using Python entry points:

```toml
[project.entry-points."ocrbridge.engines"]
ocrmac = "ocrbridge.engines.ocrmac:OcrmacEngine"
```

This allows OCR Bridge to automatically discover and load the engine at runtime.

### Core Components

- `src/ocrbridge/engines/ocrmac/engine.py` - Main `OcrmacEngine` class implementing `OCREngine` interface from `ocrbridge-core`
- `src/ocrbridge/engines/ocrmac/models.py` - `OcrmacParams` and `RecognitionLevel` enum for configuration
- `src/ocrbridge/engines/ocrmac/__init__.py` - Public API exports

### OCR Processing Flow

1. **Format validation**: Check file extension against supported formats (`.jpg`, `.jpeg`, `.png`, `.pdf`, `.tiff`, `.tif`)
2. **Platform validation**: Verify running on macOS (Darwin)
3. **LiveText validation**: For `RecognitionLevel.LIVETEXT`, verify macOS Sonoma 14.0+
4. **PDF handling**: PDFs are converted to images via `pdf2image` (300 DPI, 2 threads), then each page is processed separately
5. **OCR execution**: Use `ocrmac` library with specified `recognition_level` and `languages`
6. **HOCR conversion**: Convert ocrmac annotations (relative coords, bottom-left origin) to HOCR XML (absolute pixels, top-left origin)
7. **Multi-page merging**: For PDFs, merge individual page HOCR into single document

### Coordinate System Transformation

Critical detail in `_convert_to_hocr()` at `src/ocrbridge/engines/ocrmac/engine.py:247-311`:

- **ocrmac output**: Relative coordinates (0.0-1.0), bottom-left origin
- **HOCR format**: Absolute pixel coordinates, top-left origin
- **Y-axis flip**: `y_min = int((1.0 - bbox[1] - bbox[3]) * image_height)`

### Recognition Levels

From `src/ocrbridge/engines/ocrmac/models.py:11-28`:

- `fast`: ~131ms per image (Vision framework, fewer languages)
- `balanced`: ~150ms per image (default, Vision framework)
- `accurate`: ~207ms per image (Vision framework, highest accuracy)
- `livetext`: ~174ms per image (LiveText framework, **requires macOS Sonoma 14.0+**)

## Development Commands

This project uses `uv` for dependency management and `make` for common tasks.

### Setup
```bash
make install        # Sync dependencies including dev extras (uv sync --extra dev)
```

### Testing
```bash
make test          # Run pytest
pytest tests/test_specific.py::test_function  # Run single test
```

### Code Quality
```bash
make lint          # Run ruff linting (uv run ruff check src tests)
make format        # Format code with ruff (uv run ruff format src tests)
make typecheck     # Run pyright type checking (strict mode)
make check         # Run lint + typecheck + test
make all           # Run check + format (default target)
```

### Standards

- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Type checking**: Strict mode with pyright, Python 3.10+ compatibility
- **Python path**: `src` is added to `pythonpath` for imports
- **Ruff linting**: Rules E, F, I, N, W enabled

## Commit Messages

Follow Conventional Commits specification (enforced via `commitlint.config.js`):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat:`, `fix:`, `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`

**Breaking changes**: Use `!` suffix or `BREAKING CHANGE:` footer

## Release Process

This project uses `python-semantic-release` for automated versioning and releases. The version is stored in `pyproject.toml:project.version`.

### CI/CD Workflows

Three GitHub Actions workflows in `.github/workflows/`:
- `python-package.yml` - Runs lint, typecheck, and tests on PRs
- `conventional-commits.yml` - Validates commit message format
- `release.yml` - Automated release on push to `main` (build → test → release → deploy to PyPI)

Build command includes:
```bash
uv lock --upgrade-package "$PACKAGE_NAME"
git add uv.lock
uv build
```

## Dependencies

### Runtime
- `ocrbridge-core>=0.1.0` - Base engine interface
- `ocrmac>=0.2.2` - Apple Vision framework wrapper (macOS only)
- `pdf2image>=1.17.0` - PDF to image conversion
- `Pillow>=10.0.0` - Image processing

### Development
- `pytest~=8.0` - Testing framework
- `ruff>=0.1.0` - Linting and formatting
- `pyright>=1.1.0` - Type checking
- `pytest-cov>=7.0.0` - Coverage reporting
- `python-semantic-release>=10.5.2` - Automated releases

## Testing

### Sample Files

The `samples/` directory contains test files for development:
- `contract_de_photo.pdf`, `contract_de_scan.pdf` - German contract samples
- `contract_en_photo.pdf`, `contract_en_scan.pdf` - English contract samples
- `numbers_gs150.jpg`, `stock_gs200.jpg` - Grayscale test images

Use these for manual testing during development.

## Important Notes

- **macOS only**: This package will not work on Windows or Linux. Platform checks are enforced at runtime.
- **LiveText requirement**: `RecognitionLevel.LIVETEXT` requires macOS Sonoma 14.0+ and will raise `OCRProcessingError` on older versions.
- **Language codes**: Must be IETF BCP 47 format (e.g., `en-US`, `fr-FR`, `zh-Hans`), maximum 5 languages.
- **PDF processing**: Each PDF page creates a temporary PNG file that is deleted after processing.
- **HOCR output**: Always returns valid HOCR XML with proper DOCTYPE and namespace declarations.
