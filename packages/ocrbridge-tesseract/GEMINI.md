# OCR Bridge - Tesseract Engine (`ocrbridge-tesseract`)

## Project Overview

This project implements the Tesseract OCR engine plugin for the **OCR Bridge** architecture. It enables OCR Bridge to process images and PDFs using Google's Tesseract OCR engine, converting them into HOCR (XML) format with structured text and bounding boxes.

It is designed as a plugin that registers itself via Python entry points, allowing the main OCR Bridge system to automatically discover and use it.

**Key Technologies:**
- **Python**: >=3.10
- **Tesseract**: External binary requirement (must be installed on the OS).
- **Libraries**: `ocrbridge-core` (base interface), `pytesseract` (Python wrapper), `pdf2image` (PDF to image conversion), `Pillow`.
- **Package Manager**: `uv`.

## Architecture

### Plugin Registration
The engine is registered in `pyproject.toml` using the `ocrbridge.engines` entry point group:
```toml
[project.entry-points."ocrbridge.engines"]
tesseract = "ocrbridge.engines.tesseract:TesseractEngine"
```

### Core Components
*   **`TesseractEngine`** (`src/ocrbridge/engines/tesseract/engine.py`): The main class inheriting from `ocrbridge.core.OCREngine`. It handles the logic for:
    *   Validating input files.
    *   Converting PDFs to images (if necessary).
    *   Invoking Tesseract via `pytesseract`.
    *   Merging HOCR outputs for multi-page documents.
*   **`TesseractParams`** (`src/ocrbridge/engines/tesseract/models.py`): A Pydantic model for strictly typed configuration (language, PSM, OEM, DPI).

## Building and Running

This project uses `uv` for dependency management and a `Makefile` for common tasks.

### Prerequisites
1.  **Tesseract Binary**: Must be installed on your system (e.g., `apt-get install tesseract-ocr` or `brew install tesseract`).
2.  **uv**: Ensure `uv` is installed.

### Commands

| Task | Command | Description |
| :--- | :--- | :--- |
| **Install** | `make install` | Sync dependencies including dev extras. |
| **Test** | `make test` | Run all tests using `pytest`. |
| **Lint** | `make lint` | Run `ruff check`. |
| **Format** | `make format` | Run `ruff format`. |
| **Type Check** | `make typecheck` | Run `pyright` (strict mode). |
| **Check All** | `make check` | Run lint, typecheck, and test in sequence. |
| **Full Build**| `make all` | Run check and format. |

**Manual Alternatives (via `uv`):**
*   `uv sync --extra dev`
*   `uv run pytest`
*   `uv run ruff check src tests`

## Development Conventions

### Code Style
*   **Formatting**: Enforced by Ruff (line length: 100).
*   **Typing**: Enforced by Pyright in **strict** mode. All code must be fully typed.
*   **Imports**: Sorted and organized by Ruff (`I` rules).

### Testing
*   **Framework**: `pytest`.
*   **Markers**:
    *   `@pytest.mark.integration`: Tests that require the actual Tesseract binary to be present.
*   **Coverage**: Run with `uv run pytest --cov=src` to check coverage.

### Version Control
*   **Commit Messages**: Must follow **Conventional Commits** (e.g., `feat: ...`, `fix: ...`). Validated by `commitlint`.
*   **Branching**: Standard feature branching workflow.

### Error Handling
*   Use `OCRProcessingError` (from `ocrbridge.core`) for general processing failures.
*   Use `UnsupportedFormatError` for invalid file types.
*   Ensure Tesseract exceptions are caught and wrapped appropriately.
