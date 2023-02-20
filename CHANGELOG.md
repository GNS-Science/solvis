# Changelog


## [0.4.0] - 2022-02-21

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
