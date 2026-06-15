# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Tesseract OCR engine implementation for the OCR Bridge architecture. It's a plugin package that integrates Tesseract (Google's open-source OCR engine) with the OCR Bridge system via Python entry points. The engine processes images and PDFs, converting them to HOCR XML format with structured text and bounding boxes.

**Key dependency**: Tesseract binary must be installed on the system separately from this Python package.

## Architecture

### Plugin System
- This package registers itself as an OCR Bridge engine via entry points in `pyproject.toml`:
  ```toml
  [project.entry-points."ocrbridge.engines"]
  tesseract = "ocrbridge.engines.tesseract:TesseractEngine"
  ```
- The engine is automatically discovered by OCR Bridge at runtime
- Depends on `ocrbridge-core>=0.1.0` for base classes and interfaces

### Core Components

**TesseractEngine** (`src/ocrbridge/engines/tesseract/engine.py`):
- Main engine implementation inheriting from `ocrbridge.core.OCREngine`
- `process()` method handles both images (JPEG, PNG, TIFF) and PDFs
- PDF processing: converts pages to images via `pdf2image`, processes each with Tesseract, then merges HOCR output
- Image processing: direct Tesseract processing to HOCR format
- Multi-page PDF support with automatic page merging via `_merge_hocr_pages()`

**TesseractParams** (`src/ocrbridge/engines/tesseract/models.py`):
- Pydantic model for engine parameters with strict validation
- Validates language codes against installed Tesseract language packs (via `tesseract --list-langs`)
- Parameters: `lang` (language codes), `psm` (page segmentation 0-13), `oem` (OCR engine mode 0-3), `dpi` (PDF conversion 70-2400)
- Caches installed languages using `@functools.lru_cache` for performance

## Development Commands

### Dependency Management
Use `uv` for all package management:
```bash
# Install dependencies including dev extras
make install
# or
uv sync --extra dev
```

### Code Quality
```bash
# Run all checks (lint + typecheck + test)
make check

# Individual checks
make lint        # Ruff linting
make format      # Ruff formatting
make typecheck   # Pyright type checking
make test        # Pytest

# Run everything (check + format)
make all
```

### Running Tests
```bash
# Run all tests (including integration)
make test

# Run only unit tests (exclude integration)
uv run pytest tests/ -m "not integration"

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_models.py -v
```

### Type Checking
Pyright is configured in strict mode (`pyproject.toml`):
- `typeCheckingMode = "strict"`
- Target Python 3.10+

## Code Standards

### Linting Configuration
Ruff settings in `pyproject.toml`:
- Line length: 100 characters
- Target: Python 3.11
- Enabled rules: E (errors), F (pyflakes), I (isort), N (naming), W (warnings)

### Commit Messages
Uses Conventional Commits (enforced via commitlint):
- Format: `<type>[optional scope]: <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`
- Breaking changes: Add `!` after type/scope or use `BREAKING CHANGE:` footer
- Examples:
  - `feat(engine): add support for TIFF format`
  - `fix: correct multi-page PDF merging`
  - `docs: update installation instructions`

## Important Implementation Notes

### Error Handling
- Raise `OCRProcessingError` for processing failures (from `ocrbridge.core`)
- Raise `UnsupportedFormatError` for invalid file formats
- Always wrap Tesseract exceptions in appropriate OCR Bridge exception types

### Language Validation
- Language codes are validated against installed Tesseract language packs at runtime
- The validation is cached to avoid repeated subprocess calls
- Falls back to common languages if `tesseract --list-langs` fails
- Maximum 5 languages can be combined (e.g., `eng+fra+deu`)

### PDF Processing Flow
1. Convert PDF to images using `pdf2image.convert_from_path()` with specified DPI
2. Process each page image separately with Tesseract to get HOCR
3. Extract `<body>` content from each page's HOCR
4. Merge body content and wrap in complete HOCR XML structure
5. Include Tesseract version in merged output metadata

## Testing Requirements

- Python >=3.10 required
- Tesseract binary must be installed on the system for tests to pass
- Test files use pytest framework
- Coverage reports via pytest-cov
