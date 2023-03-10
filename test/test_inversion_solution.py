#!python3 test_inversion_solution.py

import os
import pathlib

import numpy as np
import pandas as pd
import pytest
from nzshm_common.location.location import location_by_id

from solvis import InversionSolution, circle_polygon

CRU_ARCHIVE = "ModularAlpineVernonInversionSolution.zip"
HIK_ARCHIVE = "AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
PUY_ARCHIVE = "PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip"

folder = pathlib.PurePath(os.path.realpath(__file__)).parent


@pytest.fixture(scope='class')
def puysegur_fixture(request):
    print("setup puysegur")
    filename = pathlib.PurePath(folder, f"fixtures/{PUY_ARCHIVE}")
    yield InversionSolution().from_archive(str(filename))


@pytest.fixture(scope='class')
def crustal_fixture(request):
    print("setup crustal")
    filename = pathlib.PurePath(folder, f"fixtures/{CRU_ARCHIVE}")
    yield InversionSolution().from_archive(str(filename))


class TestInversionSolution(object):
    def test_check_types(self, crustal_fixture):
        sol = crustal_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

        # print(sol.rates.dtypes)
        # print(sol.indices.dtypes)
        # print(sol.ruptures.dtypes)
        # print( sol.rates )
        assert sol.rates.index == sol.rates["Rupture Index"]
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        # print('IDX', sol.rates.index.name)
        # assert sol.indices.index == sol.indices["Rupture Index"]

        assert sol.rates["Rupture Index"].dtype == pd.UInt32Dtype()

        # assert sol.rates["fault_system"].dtype == pd.CategoricalDtype()
        assert sol.rates["Annual Rate"].dtype == np.float32
        assert sol.indices["Num Sections"].dtype == "uint16"  # pd.UInt16Dtype()
        assert sol.indices["# 1"].dtype == pd.UInt16Dtype()
        # assert 0

    def test_load_crustal_from_archive(self, crustal_fixture):
        sol = crustal_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

    def test_load_subduction_from_archive(self, puysegur_fixture):
        sol = puysegur_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'

    def test_ruptures_intersecting_crustal(self, crustal_fixture):
        sol = crustal_fixture

        WLG = location_by_id('WLG')
        # polygon = circle_polygon(5e5, -38.662334, 178.017654)
        polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 00km circle around WLG

        ruptures = sol.get_ruptures_intersecting(polygon)
        all_rupture_ids = list(sol.ruptures.index)

        assert len(sol.ruptures) > len(ruptures)
        assert set(all_rupture_ids).issuperset(set(ruptures))

    def test_new_puysegur_subduction_solution(self, puysegur_fixture):
        sol = puysegur_fixture
        new_sol = InversionSolution.filter_solution(sol, sol.ruptures)

        assert isinstance(new_sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'
        assert new_sol.fault_regime == 'SUBDUCTION'

    def test_get_ruptures_for_parent_fault(self, crustal_fixture):
        sol = crustal_fixture

        df0 = set(sol.get_ruptures_for_parent_fault("Alpine Kaniere to Springs Junction"))
        df1 = set(sol.get_ruptures_for_parent_fault("Alpine Jacksons to Kaniere"))
        print(list(df0))

        assert df0 is not df1
        assert len(df0) is not len(df1)
        assert len(df0.intersection(df1)) > 0
