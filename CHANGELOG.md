# Changelog

## [0.13.0] 2024-*

## Changed
 - drop_zero_rate differentiates between FSS and IS;
 - faster testing (~3 times faster)
 - documentation improvements
 - fix many deprecation warnings
 - updated dependencies: geopandas, pandas, numpy, pyvista libs
 - read_csv dtype configuration improvements
 - many old functions are deprecated/migrated to new filter package
 - refactor dataframe dtypes
 - standardise participation functions API and return columns
 - refactor `solvis.inversion_solution` package to `solvis.solution` and collect modules into packages
 - new packages `solvis.solution.inversion_solution` and  `solvis.solution.fault_system_solution`
 - improved test coverage
 - refactored to/from archive code to reginstate some skipped tests
 - doc/typing improvements
 - fixes to the dynamic docstrings helper class & setup
 - API simplifications
 - updated flake8 and applied many docstring fixes.

## Added
 - new filter package providing classes for filtering solutions
 - support for 3d geometry (thanks @voj)
 - simplify FSS participation using rate_weighted_mean
 - participation performance testing;
 - added participation methods to fault_system_solution
 - a simple rupture grouping algorithm (can this be a different type of filter??);
 - `pandera` library for dataframe model validations and better docs

## Removed
 - deprecated `solvis.solvis` functions removed.
 - deprecated `solvis.inversion_solution.*` functions/methods removed.

## [0.12.3] 2024-07-04
bump version to verify new pypi workflow

## [0.12.2] 2024-07-04

## [0.12.1] 2024-07-04

## Changed
 - nzshm-model to 0.10.6
 - fixes for above
 - removed twine from tox config

## [0.12.0-alpha.2] - 2024-07-03
## Changed
 - nzshm-common now ^0.8.1
 - use python3.9 compatible typing syntax (`Union` vs `|`)

## [0.12.0-alpha.1] - 2024-06-19
## Added
- `SetOperationEnum` for set joining operations
- `InversionSolutionOperations.get_rupture_ids_for_fault_names`
- `InversionSolutionOperations.get_rupture_ids_for_location_radius`
## Changed
- Updated dependencies:
    - nzhsm-common to ^0.7
    - nzshm-model to ^0.6 (will need further refactoring for higher versions)
- `circle_polygon` radius typed for float, so it can work work floats or ints
## Deprecated
- `get_ruptures_intersecting` renamed to `get_rupture_ids_intersecting`
- `get_ruptures_for_parent_fault` renamed to `get_rupture_ids_for_parent_fault`


## [0.12.0-alpha] - 2024-06-14
## Added
- Support for Python 3.10, 3.11
- MkDocs 1.6 and documentation configuration
- Docstrings, examples and type hinting for a variety of functions
- CONTRIBUTING.md
- Documentation stubs for installation, testing, usage, scripts.
- `solvis.geometry.resolve_azimuth` function for `refine_dip_direction` edge cases
## Removed
- Support for Python 3.8, soon to be EOL

## [0.11.1] - 2024-03-04
## Fixed
- mfd_hist function updated for pandas v2 compatibility

## [0.11.0] - 2023-12-13
## Changed
- remove unnecessary poetry groups from pyproject.toml
- fix missing indices error
- *.to_archive() base_archive_path can None if we already have a valid self._archive
- internal changes to _archive representation (now BytesIO)
- remove unneeded opensha artefacts from FaultSystemSolution

## Added
- FaultSystemSolution.to_archive() adds a solution/rates.csv file, with Annual rates from rate_weighted_mean aggregate.

## [0.10.0] - 2023-11-28
## Changed
- change class property names to clarify if rates are rupture rates or slip rates
- remove units from DataFrame column names

## [0.9.0] - 2023-11-24
## Added
- solution slip rate property and method (fault_sections_with_solution_slip_rates, get_solution_slip_rates_for_parent_fault)

## [0.8.1] - 2023-07-18
## Changed
- patch version bump for GHA changes

## [0.8.0] - 2023-06-28
## Added
- new solivs method parent_fault_names
- utility script for MFD calculaton checks

## [0.7.0] - 2023-04-26
## Changed
- fault_system_solution now uses fast_indices.csv instead of indices.csv
- remove dtype arg to from_csv to improve load performance

## Changed
- updated nzshm_model
- added perf test to CLI

## [0.6.0] - 2023-04
## Added
- FaultSystemSolution.filter_solution method
## Changed
- removed solvis helps new_sol and filter_solution, these must be used as the respective class methods

## [0.5.0] - 2023-03
## Added
- CompositeSolution with aggregate rates;
- to_archive() with compatible mode
- solution.filter_solution is preferred; .new_sol is deprecated;
## Changed
- InversionSolution is now composed from three modules.
- typing improvements

## [0.4.0] - 2023-02-21
## Added
- geometric surface projections from fault sections
- 3D distance calculation for both crustal and subduction subduction faults systems
- new_solution helper function in InversionSolution class (used by solvis.new_sol)
- add some performance tests using `pytest.mark.performance`
- helper functions for dip-direction, bearing etc in geometry package

## Changed
- `pytest.mark.slow` for some potentially slow tests
- surfaces now use LineString (not Polygon) for Faults with dip-deg=90. eg Fowlers
- module package refactoring

## [0.3.1] - 2022-12-22
## Changed
- refactored project structure for packaging
- changelog format for bump2version

## Added
- poetry with: pytest, coverage, tox, flake8, mypy, black, isort, bump2version

## [0.3.0] - 2022-04-05
## Changed
- improvements to mfd_hist
