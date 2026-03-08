# AGENTS.md
Working guide for autonomous coding agents in `ocrbridge-ocrmac`.

## Project Snapshot
- Package: `ocrbridge-ocrmac`
- Purpose: OCR Bridge engine backed by Apple Vision (`ocrmac`)
- Runtime: Python `>=3.10`
- Platform: macOS only (`Darwin` check is enforced in engine)
- Main code: `src/ocrbridge/engines/ocrmac/`
- Tests: `tests/`
- Entry point: `ocrbridge.engines.ocrmac:OcrmacEngine`

## Platform and Feature Constraints
- Vision recognition levels (`fast`, `balanced`, `accurate`) require macOS 10.15+
- `livetext` mode requires macOS 14+
- Do not remove or bypass platform/version validation in runtime paths

## Canonical Local Commands
Prefer `mise` wrappers because CI uses them.

Setup:
```bash
mise run install
```

Checks:
```bash
mise run lint
mise run format
mise run typecheck
mise run test
```

Aggregates:
```bash
mise run check
mise run all
```

Direct equivalents:
```bash
uv sync --extra dev
uv run ruff check src tests
uv run ruff format src tests
uv run pyright
uv run pytest
```

## Run A Single Test
Use pytest node IDs (`path::Class::test_method`).

Examples:
```bash
uv run pytest tests/test_models.py::TestOcrmacParams::test_validate_languages
uv run pytest tests/test_engine_unit.py::TestProcessMethod::test_process_routes_to_pdf_handler
```

Useful filters:
```bash
uv run pytest tests/test_engine_integration.py -m integration
uv run pytest -k livetext
uv run pytest -vv
```

## CI and Release Parity
CI workflow (`.github/workflows/python-package.yml`) runs:
```bash
mise run install
mise run lint
mise run format
mise run typecheck
mise run test
```

Release flow depends on semantic-release and lockfile staging:
```bash
uv lock --upgrade-package "$PACKAGE_NAME"
git add uv.lock
uv build
uv run semantic-release -v --strict version --skip-build
uv run semantic-release publish
```

## Style and Formatting Rules

### Ruff / imports / formatting
- Ruff is the source of truth for lint + formatting
- Line length: `100`
- Enabled lint families: `E`, `F`, `I`, `N`, `W`
- Keep import groups conventional (stdlib, third-party, local)
- Let Ruff handle import ordering/sorting

### Typing rules
- Pyright strict mode is enabled
- Prefer explicit annotations on public APIs and non-trivial locals
- Use modern type syntax (`list[str] | None`, `tuple[...]`)
- Avoid untyped public interfaces
- Existing code uses narrow `type: ignore[...]` for missing stubs; keep this rare/scoped

### Naming conventions
- Classes: `PascalCase`
- Functions/methods/variables: `snake_case`
- Constants and enum members: `UPPER_CASE`
- External enum values: lowercase strings (API-facing)
- Tests: `test_<behavior>` with specific behavior in the name

### Docstrings and comments
- Keep concise docstrings on public classes/functions and major test groups
- Add comments only for non-obvious logic
- Avoid obvious narrative comments

## Error Handling Conventions
- Use domain exceptions with actionable messages:
  - `OCRProcessingError`
  - `UnsupportedFormatError`
- Validate early (platform, params, file existence, extension, feature requirements)
- Preserve root causes with exception chaining (`raise ... from e`) when wrapping
- Include contextual details in errors when useful (platform/version/extension)

## OCR/HOCR Contract (Do Not Break)
- Coordinate systems:
  - OCR input annotations are relative and bottom-left-origin
  - HOCR output must be absolute pixels and top-left-origin
- HOCR output must retain:
  - XML declaration
  - XHTML Transitional DOCTYPE
  - XHTML namespace
  - `ocr_page` -> `ocr_line` -> `ocrx_word` hierarchy
  - bbox/confidence metadata in title attributes
- PDF flow should stay compatible:
  - `convert_from_path(..., dpi=300, thread_count=2)`
  - per-page OCR + page merge
  - temp-file cleanup in `finally`

## Test Conventions
- Unit tests are mostly mocked and should be stable across environments
- Integration tests are macOS-gated and marked with `integration`
- Some integration scenarios depend on external tooling (`pdfocr`, Poppler)
- Reuse fixtures/helpers from `tests/conftest.py`
- Assert structure and semantics, not only string presence

Recommended pre-finish gate:
```bash
mise run lint && mise run typecheck && mise run test
```

## Commit and PR Rules
- Conventional Commits are enforced in CI (`prek` + `gitlint`)
- Common prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Commit body max line length rule: `150`

## Commonly Touched Files
- `src/ocrbridge/engines/ocrmac/engine.py`
- `src/ocrbridge/engines/ocrmac/models.py`
- `src/ocrbridge/engines/ocrmac/__init__.py`
- `tests/test_engine_unit.py`
- `tests/test_engine_integration.py`
- `tests/conftest.py`

## Cursor/Copilot Instruction Files
Scanned for:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

Result: none present in this repository.
