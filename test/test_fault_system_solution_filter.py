import os
import pathlib

import nzshm_model as nm
import pytest

import solvis

# from solvis.solution.fault_system_solution import FaultSystemSolution
from solvis.filter.rupture_id_filter import FilterRuptureIds


@pytest.fixture(scope='module')
def composite_fixture(request):
    slt = nm.get_model_version("NSHM_v1.0.4").source_logic_tree
    archive = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures/TinyCompositeSolution.zip"
    yield solvis.CompositeSolution.from_archive(archive, slt)


def test_filter_from_complete_composite(composite_fixture):
    sol = composite_fixture.get_fault_system_solution('HIK')
    ruptures = list(FilterRuptureIds(sol).for_rupture_rate(min_rate=1e-7))
    print(ruptures)
    new_sol = solvis.FaultSystemSolution.filter_solution(sol, ruptures)
    assert len(ruptures) == new_sol.solution_file.ruptures.shape[0]
    # assert 0
