import geopandas as gpd
import nzshm_model as nm
import pandas as pd
import os
import pathlib
import pytest
from pandas.api.types import infer_dtype

# from solvis.inversion_solution.fault_system_solution import FaultSystemSolution

import solvis


@pytest.fixture(scope='module')
def composite_fixture(request):
    slt = nm.get_model_version("NSHM_v1.0.4").source_logic_tree()
    archive = pathlib.PurePath(os.path.realpath(__file__)).parent / f"fixtures/NSHM_v1.0.4_CompositeSolution.zip"
    yield solvis.CompositeSolution.from_archive(archive, slt)


def test_filter_from_complete_composite(composite_fixture):

    sol = composite_fixture._solutions['HIK']
    ruptures = solvis.rupt_ids_above_rate(sol, 1e-7, rate_column="rate_weighted_mean")
    new_sol = solvis.FaultSystemSolution.filter_solution(sol, ruptures)
    assert ruptures.shape[0] == new_sol.ruptures.shape[0]


def test_filter_solution_ruptures(self, crustal_small_fss_fixture):
    sol = crustal_small_fss_fixture
    ruptures = solvis.rupt_ids_above_rate(sol, 1e-7, rate_column="rate_weighted_mean")
    new_sol = solvis.FaultSystemSolution.filter_solution(sol, ruptures)
    assert ruptures.shape[0] == new_sol.ruptures.shape[0]

