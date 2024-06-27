import os
import pathlib

import nzshm_model as nm
import pytest

import solvis

# import tempfile
# from copy import deepcopy
# from test.conftest import branch_solutions
# from solvis import CompositeSolution, FaultSystemSolution

tests_folder = pathlib.PurePath(os.path.realpath(__file__)).parent
work_folder = tests_folder / ".." / "WORK"


# TODO: 1) consider class refactoring to make functions code easier to work on
# TODO: 2) do we want to break FSS opensha reporting compatability to simplify index management; what about rates?
# TODO: 3) once 2) is resolved, use this code to create the mini fixture file for further testing
# NOTE: Added dropping of opensha only files that are quite large so 2) is already broken
@pytest.mark.skip("WIP still need to properly serialise FSS with filtered tables and indexing")
def test_composite_filtering():
    slt = nm.get_model_version('NSHM_v1.0.4').source_logic_tree()
    composite_v1_0_4 = solvis.CompositeSolution.from_archive(work_folder / "NSHM_v1.0.4_CompositeSolution-M1.zip", slt)

    # folder = tempfile.TemporaryDirectory()
    print(composite_v1_0_4._solutions)

    sample_size = 10

    new_composite = solvis.CompositeSolution(slt)

    for fss_key in composite_v1_0_4.get_fault_system_codes():
        #
        fault_system_solution = composite_v1_0_4.get_fault_system_solution(fss_key)
        #
        rupts = fault_system_solution.ruptures
        rupt_ids = set(rupts['Rupture Index'].unique())
        #
        rrates = fault_system_solution.ruptures_with_rupture_rates
        rrate_ids = set(rrates['Rupture Index'].unique())
        #
        sample_no_rates = list(rrate_ids)[:sample_size]
        sample_rates = list(rupt_ids.difference(rrate_ids))[:sample_size]  # exclude no rates
        #
        new_fss = solvis.FaultSystemSolution.filter_solution(
            fault_system_solution, list(sample_no_rates + sample_rates)
        )
        new_composite.add_fault_system_solution(fss_key, new_fss)

    new_composite.to_archive(work_folder / "TinyCompositeSolution.zip")
