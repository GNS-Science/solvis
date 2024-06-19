#!python3 test_inversion_solution.py

import os
import pathlib

import numpy as np
import pandas as pd
from nzshm_common.location.location import location_by_id
from pytest import approx, raises

from solvis import InversionSolution, circle_polygon
from solvis.inversion_solution.typing import SetOperationEnum

folder = pathlib.PurePath(os.path.realpath(__file__)).parent

FSR_COLUMNS_A = 26
FSR_COLUMNS_B = 25  # HIK
RATE_COLUMNS_A = 6


class TestInversionSolution(object):
    def test_check_indexes(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert sol.rupture_rates.index == sol.rupture_rates["Rupture Index"]
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index.all() == sol.indices["Rupture Index"].all()
        assert sol.rupture_rates["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_check_types(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

        assert sol.rupture_rates["Annual Rate"].dtype == np.float32
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

    def test_get_rupture_ids_intersecting_crustal(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        WLG = location_by_id('WLG')
        # polygon = circle_polygon(5e5, -38.662334, 178.017654)
        polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG

        ruptures = sol.get_rupture_ids_intersecting(polygon)
        all_rupture_ids = list(sol.ruptures.index)

        assert len(sol.ruptures) > len(ruptures)
        assert set(all_rupture_ids).issuperset(set(ruptures))

    def test_get_rupture_ids_for_parent_fault(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        pf1_ids = set(sol.get_rupture_ids_for_parent_fault("Alpine Kaniere to Springs Junction"))
        pf2_ids = set(sol.get_rupture_ids_for_parent_fault("Alpine Jacksons to Kaniere"))
        print(list(pf1_ids))

        assert pf1_ids is not pf2_ids, "Should return different rupture ID sets"
        assert len(pf1_ids) is not len(pf2_ids), "Sets should have different lengths"
        assert len(pf1_ids.intersection(pf2_ids)) > 0, "Sets are expected to overlap"

    def test_get_rupture_ids_for_fault_names(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        PARENT_FAULT_1 = "Alpine Jacksons to Kaniere"
        PARENT_FAULT_2 = "Alpine Kaniere to Springs Junction"
        PF1_IDS = set(sol.get_rupture_ids_for_parent_fault(PARENT_FAULT_1))
        PF2_IDS = set(sol.get_rupture_ids_for_parent_fault(PARENT_FAULT_2))

        # Ensure we get the same results as when joining sets manually.

        rupture_ids_union = sol.get_rupture_ids_for_fault_names(
            corupture_fault_names=[PARENT_FAULT_1, PARENT_FAULT_2],
            fault_join_type=SetOperationEnum.UNION,
        )
        assert len(rupture_ids_union) == len(PF1_IDS.union(PF2_IDS))

        rupture_ids_intersection = sol.get_rupture_ids_for_fault_names(
            corupture_fault_names=[PARENT_FAULT_1, PARENT_FAULT_2],
            fault_join_type=SetOperationEnum.INTERSECTION,
        )

        assert len(rupture_ids_intersection) == len(PF1_IDS.intersection(PF2_IDS))

        with raises(ValueError):
            sol.get_rupture_ids_for_fault_names(
                corupture_fault_names=[PARENT_FAULT_1, PARENT_FAULT_2],
                fault_join_type=SetOperationEnum.DIFFERENCE,
            )

    def test_get_rupture_ids_for_location_radius(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        def _rupture_ids_for_location(location_id: str, radius_km: int = 100):
            """Helper: ruptures in polygon around location."""
            loc = location_by_id(location_id)
            loc_polygon = circle_polygon(radius_km * 1000, loc["latitude"], loc["longitude"])
            rupids = sol.get_rupture_ids_intersecting(loc_polygon)
            return rupids

        ruptures_wlg = _rupture_ids_for_location("WLG")
        ruptures_bhe = _rupture_ids_for_location("BHE")
        # All WLG results should also in BHE set for this fixture
        expected_intersection_ruptures = set(ruptures_wlg).intersection(ruptures_bhe)
        expected_union_ruptures = set(ruptures_wlg).union(ruptures_bhe)
        # Pre-checks on assumptions
        assert len(ruptures_wlg) == len(expected_intersection_ruptures)
        assert len(ruptures_bhe) == len(expected_union_ruptures)

        wlg_rupture_ids = sol.get_rupture_ids_for_location_radius(
            location_ids=["WLG"],
            radius_km=100,
            location_join_type=SetOperationEnum.INTERSECTION,
        )
        assert len(wlg_rupture_ids) == len(ruptures_wlg)

        intersection_rupture_ids = sol.get_rupture_ids_for_location_radius(
            location_ids=["WLG", "BHE"],
            radius_km=100,
            location_join_type=SetOperationEnum.INTERSECTION,
        )
        assert len(intersection_rupture_ids) == len(expected_intersection_ruptures)

        union_rupture_ids = sol.get_rupture_ids_for_location_radius(
            location_ids=["WLG", "BHE"],
            radius_km=100,
            location_join_type=SetOperationEnum.UNION,
        )
        assert len(union_rupture_ids) == len(expected_union_ruptures)

        with raises(ValueError):
            sol.get_rupture_ids_for_location_radius(
                location_ids=["WLG", "BHE"],
                radius_km=100,
                location_join_type=SetOperationEnum.DIFFERENCE,
            )

    def test_slip_rate_soln(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        assert (sol.average_slips.index == sol.average_slips["Rupture Index"]).all()
        assert len(sol.fault_sections_with_solution_slip_rates) == len(sol.fault_sections)
        assert sol.fault_sections_with_solution_slip_rates.loc[0, "Solution Slip Rate"] == approx(
            0.02632348565225584, abs=1e-10, rel=1e-6
        )

    def test_target_slip_rates(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        sol.section_target_slip_rates
        sol.fault_sections
        assert "Target Slip Rate" in sol.fault_sections.columns
        assert "Target Slip Rate StdDev" in sol.fault_sections.columns
        assert "SlipRate" not in sol.fault_sections.columns
        assert "SlipRateStdDev" not in sol.fault_sections.columns
        assert "Section Index" not in sol.fault_sections.columns


class TestSmallPuyInversionSolution(object):
    def test_new_puysegur_filter_solution(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        new_sol = InversionSolution.filter_solution(sol, sol.ruptures.head()["Rupture Index"])
        assert isinstance(new_sol, InversionSolution)
        print(new_sol.rupture_rates)
        print(sol.rupture_rates)

        # What is this test doing??
        assert sol.rupture_rates.head().all().all() == new_sol.rupture_rates.all().all()

    def test_check_indexes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert sol.rupture_rates.index == sol.rupture_rates["Rupture Index"]
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index.all() == sol.indices["Rupture Index"].all()
        # assert sol.rupture_rates["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_shapes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        print(sol.rupture_rates)
        assert sol.rupture_rates.shape == (10, 2)
        print(sol.indices)
        assert sol.indices.shape == (10, 273)
        print(sol.ruptures)
        assert sol.ruptures.shape == (10, 5)

    def test_fault_regime(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'
