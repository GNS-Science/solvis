## Performance hit investigation....

### HEAD


=========================================================================================== slowest 20 durations ============================================================================================
9.47s setup    test/test_composite_solution.py::TestThreeFaultSystems::test_composite_rates_shape
6.09s setup    test/test_fault_system_solution.py::TestHikurangi::test_fault_sections_with_rupture_rates_shape
5.11s call     test/test_new_inversion_solution.py::TestNewInversionSolutionSubduction::test_filter_solution_ruptures
2.99s call     test/test_fault_system_solution.py::test_from_puy_branch_solutions
2.80s call     test/test_solution_surfaces_builder.py::TestSolutionSurfacesBuilder::test_build_subduction_from_archive
2.47s call     test/test_new_inversion_solution.py::TestNewInversionSolutionSubduction::test_rupt_ids_above_rate
1.69s call     test/test_rupture_representatives.py::test_build_rupture_groups
1.68s call     test/geometry/test_geometry_performance.py::TestDipDirectionCrustal::test_calc_peformance_to_a_subduction_fault_section
1.24s call     test/geometry/test_geometry_subduction.py::TestSubductionSurface::test_subduction_rupture_surface
0.87s setup    test/test_composite_solution.py::TestThreeSmallFaultSystems::test_composite_rates_shape
0.74s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[True]
0.70s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygons_join_iterable
0.67s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[False]
0.64s call     test/test_composite_solution.py::TestThreeFaultSystems::test_fault_sections_with_rupture_rates_shape
0.40s setup    test/test_fault_system_solution.py::TestSmallHikurangi::test_fault_sections_with_rupture_rates_shape
0.36s call     test/test_new_inversion_solution.py::TestNewInversionSolutionCrustal::test_rupt_ids_above_rate
0.34s call     test/geometry/test_geometry_performance.py::TestDipDirectionCrustal::test_calc_performance_to_a_crustal_fault_section
0.32s call     test/geometry/test_geometry_distance.py::TestSurfaceDistanceCalculation::test_calc_distance_to_a_subduction_fault_section
0.30s call     test/test_fault_system_solution_filter.py::test_filter_from_complete_composite
0.30s call     test/test_fault_system_solution.py::TestHikurangi::test_fault_sections_with_rupture_rates_shape
=============================================================================== 217 passed, 22 skipped, 13 warnings in 53.94s ===============================================================================
chrisbc@tryharder-ubuntu:/GNSDATA/LIB/solvis$


#### FILTER

`poetry run pytest test/filter/ --durations 20`

=========================================================================================== slowest 20 durations ============================================================================================
9.44s setup    test/filter/test_chainable_set.py::test_chaining_a_b
0.78s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[True]
0.72s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygons_join_iterable
0.68s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[False]
0.27s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_rates[False]
0.25s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_rates[True]
0.23s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_max_mag[False]
0.22s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_mag[False]
0.21s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_rate[False]
0.18s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_parent_fault_ids
0.18s call     test/filter/test_filter_rupture_ids.py::test_filter_inversion_solution_or_model
0.17s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_max_mag[True]
0.17s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_rate[True]
0.17s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_mag[True]
0.15s setup    test/filter/test_filter_parent_fault_ids.py::test_filter_fault_system_solution_or_model
0.14s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygon_intersecting_with_drop_zero
0.13s call     test/filter/test_filter_rupture_ids.py::test_filter_fault_system_solution_or_model
0.11s call     test/filter/test_filter_parent_fault_ids.py::test_filter_inversion_solution_or_model
0.10s setup    test/filter/test_filter_parent_fault_ids.py::test_parent_fault_names_all
0.09s call     test/filter/test_filter_rupture_ids.py::test_top_level_import
================================================================================ 44 passed, 1 skipped, 4 warnings in 15.30s =================================================================================
chrisbc@tryharder-ubuntu:/GNSDATA/LIB/solvis$

### COMPARED TO ,,,

commit 71200525efd65e0f187de923c512f30637d0c2f4 (HEAD) 39.7 secs

Author: Chris Chamberlain <chrisbc@artisan.co.nz>
Date:   Thu Oct 31 14:28:35 2024 +1300

    revert version to 0.12.3

=========================================================================================== slowest 20 durations ============================================================================================
9.31s setup    test/test_composite_solution.py::TestThreeFaultSystems::test_composite_rates_shape
6.06s setup    test/test_fault_system_solution.py::TestHikurangi::test_fault_sections_with_rupture_rates_shape
2.88s call     test/test_fault_system_solution.py::test_from_puy_branch_solutions
2.79s call     test/test_solution_surfaces_builder.py::TestSolutionSurfacesBuilder::test_build_subduction_from_archive
1.99s call     test/test_new_inversion_solution.py::TestNewInversionSolutionSubduction::test_filter_solution_ruptures
1.69s call     test/geometry/test_geometry_performance.py::TestDipDirectionCrustal::test_calc_peformance_to_a_subduction_fault_section
1.67s call     test/test_rupture_representatives.py::test_build_rupture_groups
1.26s call     test/geometry/test_geometry_subduction.py::TestSubductionSurface::test_subduction_rupture_surface
0.81s setup    test/test_composite_solution.py::TestThreeSmallFaultSystems::test_composite_rates_shape
0.64s call     test/test_composite_solution.py::TestThreeFaultSystems::test_fault_sections_with_rupture_rates_shape
0.42s setup    test/test_fault_system_solution.py::TestSmallHikurangi::test_fault_sections_with_rupture_rates_shape
0.34s call     test/geometry/test_geometry_performance.py::TestDipDirectionCrustal::test_calc_performance_to_a_crustal_fault_section
0.32s call     test/geometry/test_geometry_distance.py::TestSurfaceDistanceCalculation::test_calc_distance_to_a_subduction_fault_section
0.30s call     test/test_fault_system_solution.py::TestHikurangi::test_fault_sections_with_rupture_rates_shape
0.29s setup    test/test_dataframe_serialisation.py::TestSerialisation::test_write_to_archive_compatible
0.28s call     test/test_dataframe_serialisation.py::TestSerialisation::test_write_read_archive_compatible_composite_rates
0.27s call     test/test_dataframe_serialisation.py::TestSerialisation::test_write_to_archive_compatible
0.27s call     test/test_inversion_solution.py::TestInversionSolution::test_slip_rate_soln
0.26s call     test/test_dataframe_serialisation.py::TestSerialisation::test_write_read_archive_incompatible
0.26s call     test/test_dataframe_serialisation.py::TestSerialisation::test_write_read_archive_compatible
=============================================================================== 211 passed, 22 skipped, 13 warnings in 39.70s ===============================================================================
chrisbc@tryharder-ubuntu:/GNSDATA/LIB/solvis$


#### FILTER

`poetry run pytest test/filter/ --durations 20`

-- Docs: https://docs.pytest.org/en/stable/warnings.html
=========================================================================================== slowest 20 durations ============================================================================================
9.62s setup    test/filter/test_chainable_set.py::test_chaining_a_b
0.13s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[True]
0.11s call     test/filter/test_filter_parent_fault_ids.py::test_parent_faults_for_ruptures
0.08s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygons_join_iterable
0.07s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_rates[False]
0.06s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_max_mag[False]
0.06s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_mag[False]
0.06s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_rate[False]
0.04s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_join_chain[False]
0.02s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygon_intersecting_with_drop_zero
0.02s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_polygon_intersecting
0.02s call     test/filter/test_chainable_set.py::test_set_proxy_methods_return_class_wrapper
0.01s call     test/filter/test_filter_rupture_ids.py::test_filter_invalid_polygon_join_raises
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_parent_fault_ids
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_parent_fault_names
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_all
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_rate[True]
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_max_mag[True]
0.01s call     test/filter/test_filter_rupture_ids.py::test_filter_chaining_rates[True]
0.01s call     test/filter/test_filter_rupture_ids.py::test_ruptures_for_min_mag[True]
================================================================================ 38 passed, 1 skipped, 3 warnings in 10.49s =================================================================================
chrisbc@tryharder-ubuntu:/GNSDATA/LIB/solvis$