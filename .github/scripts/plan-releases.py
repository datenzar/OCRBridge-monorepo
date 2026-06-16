#!/usr/bin/env python3
"""Plan releasable projects from workspace Semantic Release configuration."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def discover_projects() -> list[dict[str, str]]:
    root_config = load_toml(ROOT / "pyproject.toml")
    members = (
        root_config.get("tool", {})
        .get("uv", {})
        .get("workspace", {})
        .get("members", [])
    )
    projects: list[dict[str, str]] = []

    for member in members:
        project_path = ROOT / member
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            continue

        config = load_toml(pyproject_path)
        if "semantic_release" not in config.get("tool", {}):
            continue

        name = config.get("project", {}).get("name")
        if not isinstance(name, str):
            raise ValueError(f"Missing project.name in {pyproject_path}")

        projects.append({"package": name, "path": member})

    return projects


def parse_github_output(path: Path) -> dict[str, str]:
    outputs: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        if "<<" in line:
            key, delimiter = line.split("<<", 1)
            index += 1
            value_lines: list[str] = []
            while index < len(lines) and lines[index] != delimiter:
                value_lines.append(lines[index])
                index += 1
            outputs[key] = "\n".join(value_lines)
        elif "=" in line:
            key, value = line.split("=", 1)
            outputs[key] = value
        index += 1

    return outputs


def plan_project(project: dict[str, str]) -> dict[str, str] | None:
    with tempfile.NamedTemporaryFile() as github_output:
        env = os.environ.copy()
        env["GITHUB_OUTPUT"] = github_output.name

        result = subprocess.run(
            ["uv", "run", "semantic-release", "-v", "--noop", "version"],
            cwd=ROOT / project["path"],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        if result.returncode != 0:
            sys.stdout.write(result.stdout)
            raise RuntimeError(
                f"Semantic Release planning failed for {project['package']} "
                f"with exit code {result.returncode}"
            )

        outputs = parse_github_output(Path(github_output.name))

    released = outputs.get("released")
    if released is None:
        raise RuntimeError(
            "Semantic Release did not write a 'released' output for "
            f"{project['package']}. Output was:\n{result.stdout}"
        )

    if released.lower() != "true":
        print(f"No release planned for {project['package']}")
        return None

    planned = dict(project)
    for key in ("version", "tag"):
        value = outputs.get(key)
        if value:
            planned[key] = value

    print(
        f"Release planned for {project['package']}: {planned.get('version', 'unknown version')}"
    )
    return planned


def write_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as file:
            file.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only print discovered release projects without running Semantic Release.",
    )
    args = parser.parse_args()

    projects = discover_projects()
    if args.discover_only:
        print(json.dumps(projects, indent=2))
        return

    planned = [
        project
        for project in (plan_project(project) for project in projects)
        if project
    ]
    pypi_projects = [
        {
            **project,
            "pypi-url": f"https://pypi.org/project/{project['package']}/",
        }
        for project in planned
        if project["package"].startswith("ocrbridge-")
    ]
    service_projects = [
        project for project in planned if project["package"] == "ocr-service"
    ]

    write_output(
        "pypi_matrix", json.dumps({"include": pypi_projects}, separators=(",", ":"))
    )
    write_output("has_pypi", str(bool(pypi_projects)).lower())
    write_output(
        "service_matrix",
        json.dumps({"include": service_projects}, separators=(",", ":")),
    )
    write_output("has_service", str(bool(service_projects)).lower())


if __name__ == "__main__":
    main()
