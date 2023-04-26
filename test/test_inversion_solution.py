#!python3 test_inversion_solution.py

import os
import pathlib

import numpy as np
import pandas as pd
from nzshm_common.location.location import location_by_id

from solvis import InversionSolution, circle_polygon

folder = pathlib.PurePath(os.path.realpath(__file__)).parent

FSR_COLUMNS_A = 26
FSR_COLUMNS_B = 25  # HIK
RATE_COLUMNS_A = 6


class TestInversionSolution(object):
    def test_check_indexes(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert sol.rates.index == sol.rates["Rupture Index"]
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index.all() == sol.indices["Rupture Index"].all()
        assert sol.rates["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_check_types(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

        assert sol.rates["Annual Rate"].dtype == np.float32
        # assert sol.indices["Num Sections"].dtype == pd.UInt16Dtype()
        # assert sol.indices["# 1"].dtype == pd.UInt16Dtype()
        # assert 0

    def test_load_crustal_from_archive(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

    # def test_load_subduction_from_archive(self, puysegur_fixture):
    #     sol = puysegur_fixture
    #     assert isinstance(sol, InversionSolution)
    #     assert sol.fault_regime == 'SUBDUCTION'

    def test_ruptures_intersecting_crustal(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        WLG = location_by_id('WLG')
        # polygon = circle_polygon(5e5, -38.662334, 178.017654)
        polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 00km circle around WLG

        ruptures = sol.get_ruptures_intersecting(polygon)
        all_rupture_ids = list(sol.ruptures.index)

        assert len(sol.ruptures) > len(ruptures)
        assert set(all_rupture_ids).issuperset(set(ruptures))

    def test_get_ruptures_for_parent_fault(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        df0 = set(sol.get_ruptures_for_parent_fault("Alpine Kaniere to Springs Junction"))
        df1 = set(sol.get_ruptures_for_parent_fault("Alpine Jacksons to Kaniere"))
        print(list(df0))

        assert df0 is not df1
        assert len(df0) is not len(df1)
        assert len(df0.intersection(df1)) > 0


class TestSmallPuyInversionSolution(object):
    def test_new_puysegur_filter_solution(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        new_sol = InversionSolution.filter_solution(sol, sol.ruptures.head()["Rupture Index"])
        assert isinstance(new_sol, InversionSolution)
        print(new_sol.rates)
        print(sol.rates)

        # What is this test doing??
        assert sol.rates.head().all().all() == new_sol.rates.all().all()

    def test_check_indexes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert sol.rates.index == sol.rates["Rupture Index"]
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index.all() == sol.indices["Rupture Index"].all()
        # assert sol.rates["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_shapes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        print(sol.rates)
        assert sol.rates.shape == (10, 2)
        print(sol.indices)
        assert sol.indices.shape == (10, 273)
        print(sol.ruptures)
        assert sol.ruptures.shape == (10, 5)

    def test_fault_regime(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'
