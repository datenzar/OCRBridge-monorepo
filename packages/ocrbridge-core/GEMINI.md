# OCR Bridge Core

## Project Overview

`ocrbridge-core` is the foundational Python package for the OCR Bridge ecosystem. It provides the abstract base classes, data models, and utilities required to implement specific OCR engine plugins (like Tesseract, EasyOCR, etc.). The project emphasizes a modular architecture where engines can be dynamically loaded.

### Key Technologies
*   **Language:** Python 3.10+
*   **Build System:** Hatchling
*   **Task Runner:** `mise`
*   **Dependency Manager:** `uv`
*   **Linting & Formatting:** `ruff`
*   **Type Checking:** `pyright`
*   **Testing:** `pytest`
*   **Validation:** `pydantic`

## Architecture

The package is structured around these core components located in `src/ocrbridge/core/`:

*   **`base.py`:** Defines the `OCREngine` abstract base class that all plugins must inherit from. It enforces the implementation of the `process` method.
*   **`models.py`:** Contains Pydantic models like `OCREngineParams` for validating engine parameters.
*   **`exceptions.py`:** Defines a hierarchy of exceptions (`OCRBridgeError`, `OCRProcessingError`, etc.) for error handling.
*   **`utils/hocr.py`:** specific utilities for handling HOCR (HTML-based OCR) XML output, including parsing and validation.

## Building and Running

The project uses the root `mise.toml` to streamline development tasks, leveraging `uv` for environment management.

### Common Commands

*   **Install Dependencies:**
    ```bash
    mise install
    mise run install:core
    ```
    *Syncs dependencies including dev extras.*

*   **Run Tests:**
    ```bash
    mise run test:core
    ```
    *Runs the test suite using `pytest`.*

*   **Linting:**
    ```bash
    mise run lint:core
    ```
    *Checks code style and errors using `ruff`.*

*   **Formatting:**
    ```bash
    mise run format:core
    ```
    *Formats code using `ruff`.*

*   **Type Checking:**
    ```bash
    mise run typecheck:core
    ```
    *Runs static type analysis using `pyright`.*

*   **Full Check:**
    ```bash
    mise run check
    ```
    *Runs lint, typecheck, and test in sequence.*

## Development Conventions

*   **Code Style:** Strict adherence to `ruff` defaults for formatting and linting.
*   **Typing:** The code is strictly typed. `pyright` is used in strict mode (`typeCheckingMode = "strict"` in `pyproject.toml`).
*   **Testing:** Tests are located in the `tests/` directory and should cover new functionality. `pytest` is the runner.
*   **Project Structure:** Source code is under `src/` to support standard Python packaging layouts.
*   **Dependency Management:** `uv` is the authoritative tool for managing the root workspace lockfile (`../../uv.lock`). Always use `uv add` or `uv sync` rather than manual pip installs.
