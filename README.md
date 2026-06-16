# OCRBridge Monorepo

This repository contains the OCRBridge Python packages and OCR API service in one uv workspace.

## Layout

- `packages/ocrbridge-core` - shared OCR engine interfaces and utilities
- `packages/ocrbridge-tesseract` - Tesseract OCR engine package
- `packages/ocrbridge-easyocr` - EasyOCR engine package
- `packages/ocrbridge-ocrmac` - Apple Vision/ocrmac engine package for macOS
- `apps/ocr-service` - FastAPI OCR service

The package source trees remain separate because each package is published as its own distribution and contributes to the `ocrbridge` namespace.

## Setup

```bash
mise install
mise run install:all
```

For the service with all optional engine extras:

```bash
mise run install:service:all-engines
```

## Workflow Choices

Use `mise` for the default contributor workflow. `mise.toml` is the task source of truth for pinned tools, dependency installation, checks, local service runs, and Docker commands.

```bash
mise install
mise run install:all
mise run doctor
mise run check:fast
mise run check
```

`mise run check:fast` runs linting, formatting, type checks, and deterministic tests that avoid real EasyOCR model downloads and macOS-only OCR E2E tests. `mise run check` remains the full local gate and expects external OCR tools and model caches to be available. Run `mise run doctor` first when setting up a host.

Use Nix flakes when you need reproducible development shells, package and app outputs, or the NixOS/nix-darwin service modules.

```bash
nix develop
nix build .#ocr-service-lite
nix run .#ocr-service-lite
```

On Darwin, the Nix development shells set `TMPDIR` to a repo-local `.tmp` directory because Nix-provided Tesseract can fail to read OCR temp images from `/tmp`. The shells also set `EASYOCR_MODULE_PATH` to a repo-local `.cache/easyocr` directory to keep EasyOCR model downloads out of the shared home cache.

Use Docker or Podman for containerized service deployment through the existing Dockerfile and Compose stack.

```bash
mise run docker:doctor
mise run docker:service:lite
mise run compose:service:lite
```

The `ocrmac` engine is native macOS-only and is not included in Linux containers.

## Common Commands

```bash
mise run doctor
mise run lint
mise run format-check
mise run typecheck
mise run test:fast
mise run test
mise run check:fast
mise run check
```

Target one project with names such as `mise run test:core`, `mise run test:tesseract`, `mise run test:easyocr`, `mise run test:ocrmac`, or `mise run test:service`.

## Service

Run the API locally:

```bash
mise run dev:service
```

Build Docker images from the repository root:

```bash
mise run docker:doctor
mise run docker:service:lite
mise run docker:service:full
```

Run compose stacks from the repository root:

```bash
mise run compose:service:lite
mise run compose:service:full
```

## Releases

Package release tags are package-prefixed to avoid collisions in the monorepo, for example `ocrbridge-core-v3.1.1` and `ocrbridge-tesseract-v3.0.1`.

Python Semantic Release configuration lives in each package `pyproject.toml` and uses monorepo path filters so a package only releases for changes under its own directory.
