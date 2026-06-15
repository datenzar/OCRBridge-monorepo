UV := uv
RUFF := ruff
PYRIGHT := pyright

DEFAULT_GOAL := all

help:
	@printf "Available targets:\n"
	@printf "  %-12s%s\n" "install" "sync dependencies (includes dev extras)"
	@printf "  %-12s%s\n" "lint" "ruff lint checks"
	@printf "  %-12s%s\n" "format" "ruff formatter"
	@printf "  %-12s%s\n" "typecheck" "pyright"
	@printf "  %-12s%s\n" "test" "pytest"
	@printf "  %-12s%s\n" "check" "lint + typecheck + test"
	@printf "  %-12s%s\n" "all" "check + format"

install:
	$(UV) sync --group dev

lint: install
	$(UV) run $(RUFF) check src tests

format: install
	$(UV) run $(RUFF) format src tests

typecheck: install
	$(UV) run $(PYRIGHT) --project pyproject.toml

test: install
	$(UV) run pytest

check: lint typecheck test

all: check format

.PHONY: install lint format typecheck test check all help
