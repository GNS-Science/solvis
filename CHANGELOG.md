# Changelog

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
