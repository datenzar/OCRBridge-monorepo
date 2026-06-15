# OCR Bridge - ocrmac Engine

`ocrbridge-ocrmac` is an OCR Bridge engine backed by Apple's Vision framework via `ocrmac`.

## Overview

This package plugs into OCR Bridge through Python entry points and provides HOCR output for images and PDFs on macOS.

Entry point registration (from `pyproject.toml`):

```toml
[project.entry-points."ocrbridge.engines"]
ocrmac = "ocrbridge.engines.ocrmac:OcrmacEngine"
```

## Features

- Native Apple OCR via Vision framework
- LiveText mode support on newer macOS versions
- Input formats: JPEG, PNG, TIFF, PDF
- HOCR XML output with bbox and confidence metadata
- Automatic plugin discovery in OCR Bridge

## Platform Requirements

- macOS only (runtime enforces `Darwin`)
- macOS 10.15+ for Vision modes (`fast`, `balanced`, `accurate`)
- macOS 14.0+ for `livetext`

This package will not run on Linux or Windows.

## Installation

```bash
pip install ocrbridge-ocrmac
```

Compatibility quick check:

- Python `>=3.10`
- macOS `>=10.15` (`>=14.0` for `livetext`)
- Key runtime deps: `ocrbridge-core>=3.1.0`, `ocrmac>=0.2.2`

## Usage

The engine is discovered automatically by OCR Bridge, or you can import and use it directly.

### Public API

Stable imports from this package:

- `OcrmacEngine`
- `OcrmacParams`
- `RecognitionLevel`

### Parameters

- `languages` (`list[str] | None`): IETF BCP 47 codes (for example `"en-US"`, `"zh-Hans"`)
- `recognition_level` (`RecognitionLevel`): `fast`, `balanced`, `accurate`, `livetext`

Defaults:

- `languages=None` (auto-detect)
- `recognition_level=RecognitionLevel.BALANCED`

### Example

```python
from pathlib import Path

from ocrbridge.engines.ocrmac import OcrmacEngine, OcrmacParams, RecognitionLevel

engine = OcrmacEngine()

# Process with defaults
hocr = engine.process(Path("document.pdf"))

# Process with custom parameters
params = OcrmacParams(
    languages=["en-US", "fr-FR"],
    recognition_level=RecognitionLevel.ACCURATE,
)
hocr = engine.process(Path("document.pdf"), params)

# LiveText (requires macOS 14+)
params_livetext = OcrmacParams(
    languages=["en-US"],
    recognition_level=RecognitionLevel.LIVETEXT,
)
hocr = engine.process(Path("document.pdf"), params_livetext)
```

## Integration (Entry Points)

This package exposes one OCR Bridge engine entry point:

- Group: `ocrbridge.engines`
- Name: `ocrmac`
- Target: `ocrbridge.engines.ocrmac:OcrmacEngine`

### Verify discovery in your environment

If the package is installed but not discovered, run:

```python
from importlib.metadata import entry_points

eps = entry_points()
group = "ocrbridge.engines"

if hasattr(eps, "select"):
    engines = eps.select(group=group)
else:
    engines = eps.get(group, [])

for ep in engines:
    print(f"{ep.name} -> {ep.value}")
```

## Supported Input Formats

- `.jpg`
- `.jpeg`
- `.png`
- `.pdf`
- `.tiff`
- `.tif`

## Development

This repository uses `uv` for Python environments/dependencies and `mise` for task aliases.

### Setup

```bash
mise run install
```

### Quality and Tests

```bash
mise run lint
mise run format
mise run typecheck
mise run test
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

### Run a Single Test

Use pytest node IDs:

```bash
uv run pytest tests/test_models.py::TestOcrmacParams::test_validate_languages
uv run pytest tests/test_engine_unit.py::TestProcessMethod::test_process_routes_to_pdf_handler
```

Useful filters:

```bash
uv run pytest tests/test_engine_integration.py -m integration
uv run pytest -k livetext
```

## Notes on Output and Processing

- Output is HOCR XML (XHTML doctype + namespace)
- OCR annotations are converted from relative bottom-left coordinates to absolute top-left pixel coordinates
- PDFs are rasterized to page images (300 DPI) and merged back into a multi-page HOCR document

## Release and CI

- CI runs on macOS and uses `mise` tasks for lint/format/typecheck/test
- Releases are automated with `python-semantic-release`
- Commit messages follow Conventional Commits (validated in CI)

## Troubleshooting

- Engine not discovered: confirm you installed in the active environment, then run the discovery snippet above.
- `livetext` fails: verify macOS major version is 14 or newer.
- Non-macOS runtime: expected failure; this engine intentionally supports macOS only.
- PDF OCR issues: ensure Poppler is available when your workflow depends on PDF rasterization tooling.

## Contributing

See `CONTRIBUTING.md` for contribution workflow and commit message guidance.
