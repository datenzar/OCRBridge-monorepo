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

## Common Commands

```bash
mise run lint
mise run format-check
mise run typecheck
mise run test
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
