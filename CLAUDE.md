# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Solvis is a Python library for analysis of OpenSHA Modular Fault System Solution files, used for New Zealand National Seismic Hazard Model (NSHM) research. License: AGPL-3.0-or-later.

## Development Commands

### Setup
```
pyenv local 3.10
poetry env use 3.10
poetry sync --all-groups
```

### Testing
- `poetry run pytest` — run all tests
- `poetry run pytest test/<file>.py` — run a single test file
- `poetry run pytest -k <keyword>` — filter tests by name
- `poetry run tox` — full QA suite (tests across Python 3.10/3.11/3.12, lint, format)
- `poetry run tox -e py310` — tests with coverage for a specific Python version

### Code Quality
- `poetry run tox -e format` — apply formatting (black + isort)
- `poetry run tox -e lint` — lint and type checking (flake8 + mypy)
- `poetry run black solvis test` — format code (line-length 120, skip string normalization)
- `poetry run isort solvis test` — sort imports
- `poetry run mypy solvis test` — type checking (uses pandera plugin)

### Documentation
- `mkdocs serve` — preview docs locally

## Architecture

### Core Classes (solvis/solution/)
- **InversionSolution** (`inversion_solution/`) — interface to a single OpenSHA inversion solution archive (zip file). Loads ruptures, fault sections, rates as DataFrames.
- **FaultSystemSolution** (`fault_system_solution/`) — aggregates multiple InversionSolutions sharing the same rupture set.
- **CompositeSolution** (`composite_solution.py`) — container for a complete NSHM model and its logic tree.

All three are exported from `solvis/__init__.py`.

### Filters (solvis/filter/)
Chainable, set-like filter classes for selecting ruptures:
- `RuptureIdFilter` — filter by rupture ID
- `ParentFaultIdFilter` — filter by parent fault
- `SubsectionIdFilter` — filter by subsection
- All inherit from `ChainableSetBase` and support set operations (union, intersection, difference).

### Key Modules
- `solvis/solution/dataframe_models.py` — Pandera DataFrameModel schemas for runtime DataFrame validation
- `solvis/solution/solution_participation.py` — rupture participation rate calculations
- `solvis/solution/solution_surfaces_builder.py` — geometry building for fault surfaces
- `solvis/solution/typing.py` — Protocol definitions for interfaces
- `solvis/geometry.py` — geometric calculations (Shapely-based; optional pyvista for 3D)
- `solvis/utils.py` — utilities including MFD histogram generation and GeoJSON export
- `solvis/scripts/cli.py` — Click-based CLI

### Dependencies
Core: geopandas, pandas, pandera, pyproj, nzshm-common, nzshm-model. Optional: pyvista (vtk extra), shapely (demo extra).

## Code Conventions

- **Line length:** 120 characters
- **Docstrings:** Google style
- **Formatting:** black (skip-string-normalization) + isort
- **Linting:** flake8 (max-complexity 18) + mypy with pandera plugin
- **Test framework:** pytest with markers: `slow`, `performance`, `TODO_check_values`
- **Test fixtures:** test archives in `test/fixtures/`; fixtures defined in `test/conftest.py`
- **DataFrame validation:** Use Pandera DataFrameModel schemas for any new DataFrame structures
- **TYPE_CHECKING guards:** Used throughout for imports only needed by type checkers
