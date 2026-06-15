# AGENTS.md

## Start Here
- Use `mise` from the repository root for normal workflows; `mise.toml` is the command source of truth, not the package-local `Makefile`s or older package instruction files.
- Install pinned tools first with `mise install`, then install dependencies with `mise run install:all` or a narrower task such as `mise run install:service:all-engines`.
- The root is a `uv` workspace; keep dependency and lockfile changes in the root `pyproject.toml` / `uv.lock` unless a package `pyproject.toml` is the real source of the change.

## Workspace Shape
- Workspace members are `packages/ocrbridge-core`, `packages/ocrbridge-tesseract`, `packages/ocrbridge-easyocr`, `packages/ocrbridge-ocrmac`, and `apps/ocr-service`.
- The packages intentionally share the `ocrbridge` namespace but publish as separate distributions; avoid flattening source trees or assuming one package owns the whole namespace.
- Engine packages register plugins via `[project.entry-points."ocrbridge.engines"]`; the FastAPI service discovers installed engines at startup instead of importing hardcoded engines.

## Commands
- Full local gate: `mise run check` runs lint, format check, type checks, and tests for all workspace projects.
- Focused package gates: `mise run lint:core`, `mise run format-check:core`, `mise run typecheck:core`, `mise run test:core`; replace `core` with `tesseract`, `easyocr`, `ocrmac`, or `service`.
- Format code with `mise run format` or a focused `mise run format:<name>`; CI checks formatting with `format-check`, not `format`.
- Run one test directly through the package directory, for example `uv --directory packages/ocrbridge-tesseract run pytest tests/test_models.py::test_name` or `uv --directory apps/ocr-service run pytest tests/unit/api/test_dynamic_routes.py::test_name`.
- Build the service locally from the repo root with `mise run docker:service:lite` or `mise run docker:service:full`; compose stacks are `mise run compose:service:lite` and `mise run compose:service:full`.
- Run the API locally with `mise run dev:service` (`uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`).

## CI Parity
- Package CI runs Linux jobs for core, tesseract, and easyocr using `uv sync --locked --package <pkg> --group dev`, then Ruff, Pyright, and pytest in each package directory.
- `ocrbridge-ocrmac` CI runs on macOS and uses `mise run install:pdfocr`, `install:ocrmac`, `lint:ocrmac`, `format-check:ocrmac`, `typecheck:ocrmac`, and `test:ocrmac`.
- Service CI installs Linux system deps (`tesseract-ocr`, `poppler-utils`, `libmagic1`), runs `mise run install:service:all-engines`, then `lint:service`, `typecheck:service`, and `test:service`.
- Commit linting is Node-only: root `package.json` exists for `@commitlint/*`, and CI runs `npm ci` then `npx commitlint` on PR commits.

## Service Wiring
- Service entrypoint is `apps/ocr-service/src/main.py`; lifespan creates `EngineRegistry`, stores it on `app.state.engine_registry`, then calls `register_engine_routes()`.
- Dynamic service endpoints are generated in `src/api/routes/v2/dynamic_routes.py`: `/v2/ocr/{engine}/process`, `/v2/ocr/{engine}/info`, `/v2/ocr/engines`, and `/v2/ocr/engines/{engine_name}`.
- `EngineRegistry` discovers entry points from `ocrbridge.engines`, lazy-instantiates engines, tracks parameter models, and applies a circuit breaker; tests can inject engines through its public `inject_*` helpers.
- Parameter model discovery expects `{EngineClassName without Engine}Params` exported from the engine package module, or an explicit `__param_model__`, or a typed `process(..., params=...)` hint.
- Service settings are environment variables loaded by Pydantic Settings from `.env`; `TESTING=true` disables rate limiting in tests.

## Engine Contracts
- Every engine must subclass `ocrbridge.core.OCREngine` and implement `process(Path, OCREngineParams | None) -> str`, `name`, and `supported_formats`.
- Engine params subclass `OCREngineParams`, which forbids unknown fields; request form params are validated against the engine Pydantic model before `process()` is called.
- All engines return HOCR XML with `ocr_page` / `ocrx_word` structure and bbox metadata; multi-page PDFs are rasterized and merged into one HOCR document.
- Tesseract params use language strings like `eng+fra`; EasyOCR params use list codes like `['en', 'ch_sim']`; ocrmac params use IETF BCP 47 codes like `['en-US']`.
- Preserve domain exceptions from core (`OCRProcessingError`, `UnsupportedFormatError`, etc.) so the service can translate failures consistently.

## External Requirements
- Tesseract engine and related tests need the `tesseract` binary and language data installed outside Python.
- PDF processing needs Poppler (`poppler-utils` on Linux, `brew install poppler` on macOS) because PDF pages are rasterized before OCR.
- EasyOCR installs PyTorch and is large; it auto-detects CUDA and falls back to CPU, but its engine instance caches a reader by language set.
- `ocrbridge-ocrmac` is macOS-only; keep Darwin and macOS version checks, and remember `livetext` requires macOS 14+.
- Service `output_format=pdf` uses external `pdfocr` for PDF uploads (`mise run install:pdfocr`) and `pytesseract` for image uploads.

## Docker Notes
- `apps/ocr-service/Dockerfile` has `lite` and `full` targets; `lite` is Tesseract-only, `full` adds EasyOCR, and neither includes `ocrmac` because Docker is Linux.
- Compose maps host port `8080` to container port `8000` and overlays local `apps/ocr-service/src` plus `packages` for development.

## Releases
- Package releases are scoped by semantic-release path filters and package-prefixed tags such as `ocrbridge-core-v3.1.1`.
- Package release build commands update `uv.lock` from the repo root and run `uv build --package <package>`; do not hand-edit release tags or version files without checking the package `pyproject.toml` semantic-release config.
