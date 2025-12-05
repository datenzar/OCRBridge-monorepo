.PHONY: install lint format typecheck test check all help

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
	uv sync --group dev

lint: install
	uv run ruff check

format: install
	uv run ruff format

typecheck: install
	uv run pyright

test: install
	uv run pytest

check: lint typecheck test

all: check format
