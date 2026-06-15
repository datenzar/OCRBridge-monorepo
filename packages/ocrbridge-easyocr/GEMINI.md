# OCR Bridge - EasyOCR Engine

## Project Overview
`ocrbridge-easyocr` is a Python-based plugin for the [OCR Bridge](https://github.com/OCRBridge/ocr-service) architecture. It integrates the [EasyOCR](https://github.com/JaidedAI/EasyOCR) library to provide deep learning-based Optical Character Recognition (OCR) capabilities.

**Key Features:**
*   **Plugin Architecture:** Implements the `OCREngine` interface from `ocrbridge-core`.
*   **Deep Learning:** Uses EasyOCR (powered by PyTorch) for high-accuracy text recognition.
*   **Multilingual:** Supports 80+ languages, with a focus on Asian scripts.
*   **GPU Acceleration:** Automatically detects and utilizes CUDA GPUs via PyTorch.
*   **Format Support:** Handles images (JPG, PNG, TIFF) and PDFs (via `pdf2image`).
*   **Standard Output:** Produces HOCR (HTML-based XML) output with bounding boxes.

## Development Setup

### Prerequisites
*   **Python:** 3.10+
*   **Package Manager:** `uv` (Unified Python packaging)
*   **System Libraries:**
    *   `poppler-utils` (Required by `pdf2image` for PDF processing)
    *   CUDA-compatible GPU drivers (Optional, for GPU acceleration)

### Building and Running
This project uses a `Makefile` to orchestrate common development tasks, wrapping `uv` commands.

| Command | Description |
| :--- | :--- |
| `make install` | Install dependencies, including dev extras. |
| `make test` | Run the test suite using `pytest`. |
| `make lint` | Run `ruff` for code linting. |
| `make format` | Format code using `ruff`. |
| `make typecheck` | Run static type checking with `pyright`. |
| `make check` | Run all quality checks: `lint`, `typecheck`, and `test`. |
| `make all` | Run `check` and `format`. |
| `uv build` | Build the distribution packages (wheel/sdist). |

### Architecture
*   **Entry Point:** The engine is registered via `project.entry-points` in `pyproject.toml` as `ocrbridge.engines.easyocr:EasyOCREngine`.
*   **Core Logic:** `src/ocrbridge/engines/easyocr/engine.py` contains the `EasyOCREngine` class.
    *   `_create_reader`: Initializes the EasyOCR reader (lazy-loaded).
    *   `process`: Main method to handle files; routes to `_process_image` or `_process_pdf`.
    *   `_to_hocr`: Converts EasyOCR's specific output format to standard HOCR XML.
*   **Configuration:** `src/ocrbridge/engines/easyocr/models.py` defines `EasyOCRParams` (languages, thresholds) using Pydantic.

## Development Conventions

### Code Style
*   **Formatting:** Enforced by `ruff`. Line length is 100 characters.
*   **Typing:** Strict type checking with `pyright`. All public functions must have type annotations.
*   **Imports:** Sorted and organized by `ruff`.

### Testing
*   **Framework:** `pytest`.
*   **Location:** Tests are located in the `tests/` directory.
*   **Markers:**
    *   `@pytest.mark.integration`: Tests requiring external binaries (e.g., Tesseract, though this is EasyOCR repo, the marker exists in config).
    *   `@pytest.mark.slow`: Long-running tests.
*   **Samples:** `samples/` directory contains test assets (images, PDFs).

### Versioning & Release
*   **Semantic Versioning:** Managed by `python-semantic-release`.
*   **Commits:** Must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification (e.g., `feat:`, `fix:`, `docs:`). This is enforced by `commitlint` (via Node.js hooks) and checked in CI.
