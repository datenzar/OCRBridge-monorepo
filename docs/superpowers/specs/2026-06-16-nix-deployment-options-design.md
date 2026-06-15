# Nix Deployment Options Design

## Context

OCRBridge is a Python monorepo managed as a `uv` workspace. The repository already uses
`mise` as the canonical contributor workflow and already provides Docker/Compose service
deployment for the FastAPI OCR service.

The project needs first-class options for two user groups:

- Contributors who use `mise` and want the current workflow to remain stable.
- NixOS and nix-darwin users who want reproducible development and declarative service
  deployment through Nix.

The project also needs to keep container deployment available for Docker and Podman users.
Containers remain Dockerfile/Compose-based; Nix will not build OCI images in this phase.

## Goals

- Keep `mise` as the documented cross-platform development path.
- Add pure Nix flake package outputs for the OCR service and supported engine flavors.
- Add reusable NixOS and nix-darwin service modules.
- Keep the existing Dockerfile and Compose workflow as the container deployment path.
- Document the workflow choice clearly so users can pick `mise`, Nix, or containers without
  guessing which path is preferred for their platform.

## Non-Goals

- Do not replace `mise` tasks.
- Do not remove or rewrite the existing Dockerfile or Compose files.
- Do not build container images with Nix in this phase.
- Do not support `ocrmac` inside containers or Linux service packages.
- Do not add Home Manager integration unless a concrete user requirement appears later.

## Engine and Platform Constraints

- `ocrbridge-tesseract` requires the `tesseract` binary and language data.
- PDF handling requires Poppler utilities.
- The service uses `python-magic`, which requires `libmagic` at runtime.
- `ocrbridge-easyocr` brings PyTorch and is substantially larger than the Tesseract-only
  flavor.
- `ocrbridge-ocrmac` is Darwin-only and relies on native macOS frameworks. It belongs in the
  nix-darwin/native macOS path, not in Linux containers or Linux NixOS service packages.
- Searchable PDF output for PDF uploads can use the external `pdfocr` command, built from Go.

## Flake Architecture

Add a root `flake.nix` and checked-in `flake.lock`.

Inputs should include:

- `nixpkgs`, pinned through `flake.lock`.
- `flake-utils` or an equivalent small systems helper.
- `pyproject-nix`.
- `uv2nix`.
- `pyproject-build-systems`.

The flake should use `uv2nix` and `pyproject.nix` to build Python environments from the
existing `pyproject.toml` files and `uv.lock`. Runtime packages must be Nix derivations, not
wrappers that call `uv sync` or rely on an ambient virtual environment.

The Python package set should be assembled once per supported system and shared by packages,
apps, checks, and modules. Project-specific overrides may be needed for packages with external
runtime dependencies such as Tesseract, Poppler, `libmagic`, PyTorch, or macOS frameworks.

## Package Outputs

Expose these package outputs where supported by platform:

- `packages.<system>.ocr-service-lite`: service package with Tesseract support.
- `packages.<system>.ocr-service-full`: service package with Tesseract and EasyOCR support.
- `packages.<system>.ocr-service-macos`: Darwin-only service package with ocrmac support.
- `packages.<system>.default`: alias to `ocr-service-lite`.

The package outputs should provide runnable commands or a runtime environment that includes the
service and required system tools on `PATH`. The lite package should stay small and avoid
EasyOCR/PyTorch dependencies. The full package should include EasyOCR and remain opt-in.

The macOS package should only evaluate on Darwin systems. Linux users should not see a broken
`ocr-service-macos` output during normal flake checks.

## App Outputs

Expose app wrappers for local execution:

- `apps.<system>.ocr-service-lite`
- `apps.<system>.ocr-service-full`
- `apps.<system>.ocr-service-macos` on Darwin only
- `apps.<system>.default` as an alias to `ocr-service-lite`

Each app should run Uvicorn against `src.main:app` with sensible defaults matching the existing
service behavior:

- host: `0.0.0.0`
- port: `8000`
- workers: `4`

Configuration should continue to be environment-variable driven so the Nix app path matches the
existing service configuration model.

## Development Shells

Expose these development shells:

- `devShells.<system>.default`: standard contributor shell with Python, uv, Node, Go, Ruff,
  Pyright, ty, pytest, Tesseract, Poppler, `libmagic`, and Docker/Compose client tools when
  available in nixpkgs.
- `devShells.<system>.lite`: smaller shell for Tesseract-only service work.
- `devShells.<system>.full`: shell that includes EasyOCR/PyTorch support.
- `devShells.<system>.macos`: Darwin-only shell that includes ocrmac dependencies.

The default shell should make Nix-provided tools available without replacing the documented
`mise` flow. Documentation should present `nix develop` as an alternative for Nix users, not as a
replacement for `mise`.

## NixOS Module

Expose `nixosModules.ocr-service`.

The module should define an `ocrbridge.ocr-service` option namespace with at least:

- `enable`
- `flavor`, allowing `lite` or `full`
- `package`, allowing users to override the selected package
- `host`
- `port`
- `workers`
- `logLevel`
- `logFormat`
- `uploadDir`
- `resultsDir`
- `maxUploadSizeMb`
- `syncTimeoutSeconds`
- `syncMaxFileSizeMb`
- `rateLimitRequests`
- `pdfocrCommand`
- `user`
- `group`

When enabled, the module should create a systemd service that runs the selected package's app
wrapper. It should create or declare state/runtime directories for uploads and results with
appropriate ownership. Service environment variables should map directly to the existing
Pydantic settings used by the FastAPI service.

The module should default to the lite package. Full/EasyOCR deployment should be opt-in because
of dependency size and resource use.

## nix-darwin Module

Expose `darwinModules.ocr-service`.

The module should define the same `ocrbridge.ocr-service` option namespace where practical. It
should use `launchd.daemons` to run the service and pass environment variables explicitly.

The Darwin module should support these flavors:

- `lite`
- `full`
- `macos`

The `macos` flavor should select the Darwin-only package with ocrmac support. Any options that
are not meaningful on macOS should either be omitted or documented as no-ops. The module should
not pretend to provide Linux container behavior on macOS; Docker/Podman users should continue to
use the existing container path.

## Container Deployment

The existing container workflow remains the supported container path:

- `mise run docker:service:lite`
- `mise run docker:service:full`
- `mise run compose:service:lite`
- `mise run compose:service:full`

Documentation should state that Docker and Podman users should use the Dockerfile/Compose path.
Nix packages and modules are for native Nix deployment. Nix-built OCI images are intentionally
out of scope for this phase.

## Documentation Plan

Update the root README and service README with a "Choose Your Workflow" section:

- `mise`: fastest contributor path and the task source of truth.
- `nix develop`: reproducible Nix development shell.
- `nix run`: local service execution from flake app outputs.
- NixOS module: declarative Linux host deployment.
- nix-darwin module: declarative macOS host deployment, including native ocrmac support.
- Docker/Podman: containerized deployment via existing Dockerfile/Compose commands.

The docs should include platform-specific notes for Tesseract, EasyOCR, Poppler, `libmagic`,
`pdfocr`, and ocrmac.

## Validation Plan

Required local validation for the implementation:

- `nix flake check`
- `nix build .#ocr-service-lite`
- `nix build .#ocr-service-full`
- `nix run .#ocr-service-lite -- --help` or an equivalent lightweight command check if the app
  wrapper supports it
- `mise run check`
- `mise run docker:service:lite`

Darwin-specific validation when available:

- `nix build .#ocr-service-macos`
- `nix develop .#macos`
- Evaluate or activate a minimal nix-darwin configuration using `darwinModules.ocr-service`

NixOS-specific validation when available:

- Evaluate a minimal NixOS test configuration importing `nixosModules.ocr-service`
- Confirm the generated systemd service contains the expected environment variables and package
  path

## Risks and Mitigations

- Python dependency conversion through `uv2nix` may require package overrides. Keep overrides
  isolated under `nix/` and document why each exists.
- EasyOCR/PyTorch may be expensive to evaluate or build. Keep the full package opt-in and avoid
  making it the default output.
- Darwin-only ocrmac support can fail if evaluated on Linux. Guard macOS outputs with platform
  checks.
- Duplicate workflow documentation can drift. Root README should summarize choices; service docs
  should hold detailed commands.
- Container and Nix service behavior can diverge. Keep both paths environment-variable driven and
  use the same service settings.

## Open Implementation Decisions

- Exact supported system list should be chosen during implementation based on nixpkgs package
  availability for Python 3.14, PyTorch, Tesseract, Poppler, and `libmagic`.
- The implementation should verify whether Python 3.14 is practical in nixpkgs for all required
  dependencies. If not, use the newest nixpkgs Python that satisfies project constraints and
  document the difference from `mise.toml`.
- The final module option names should follow Nix conventions even where environment variable
  names use uppercase service settings.
