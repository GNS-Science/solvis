import os
import pathlib

import nzshm_model as nm
import pytest

import solvis

# from solvis.inversion_solution.fault_system_solution import FaultSystemSolution


@pytest.fixture(scope='module')
def composite_fixture(request):
    slt = nm.get_model_version("NSHM_v1.0.4").source_logic_tree
    archive = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures/TinyCompositeSolution.zip"
    yield solvis.CompositeSolution.from_archive(archive, slt)


def test_filter_from_complete_composite(composite_fixture):
    """
    reproduce KeyError: "There is no item named 'ruptures/indices.csv' in the archive"
    """
    sol = composite_fixture.get_fault_system_solution('HIK')
    ruptures = solvis.rupt_ids_above_rate(sol, 1e-4, rate_column="rate_weighted_mean")

    print(ruptures)

    new_sol = solvis.FaultSystemSolution.filter_solution(sol, ruptures)

    assert ruptures.shape[0] == new_sol.ruptures.shape[0]
