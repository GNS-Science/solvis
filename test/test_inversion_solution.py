#!python3 test_inversion_solution.py

import io
import os
import pathlib

import pandas as pd
import pytest
from pytest import approx

from solvis import InversionSolution

folder = pathlib.PurePath(os.path.realpath(__file__)).parent

FSR_COLUMNS_A = 26
FSR_COLUMNS_B = 25  # HIK
RATE_COLUMNS_A = 6


class TestInversionSolution(object):
    def test_check_indexes(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert sol.solution_file.indices.index.all() == sol.solution_file.indices["Rupture Index"].all()
        assert sol.solution_file.rupture_rates.index == sol.solution_file.rupture_rates["Rupture Index"]
        assert sol.solution_file.ruptures.index == sol.solution_file.ruptures["Rupture Index"]
        assert sol.solution_file.rupture_rates["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.solution_file.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_check_types(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.solution_file.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"
        assert sol.solution_file.rupture_rates["Annual Rate"].dtype == pd.Float32Dtype()
        # assert sol.indices["Num Sections"].dtype == pd.UInt16Dtype()
        # assert sol.indices["# 1"].dtype == pd.UInt16Dtype()
        # assert 0

    def test_from_archive_instance(self):
        filename = folder / "fixtures" / 'CrustalSmallSolution_compat.zip'
        instance = io.BytesIO(open(filename, 'rb').read())
        sol = InversionSolution.from_archive(instance)
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.solution_file.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

    def test_load_crustal_from_archive(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'CRUSTAL'
        assert sol.solution_file.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

    def test_slip_rate_soln(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        assert (sol.solution_file.average_slips.index == sol.solution_file.average_slips["Rupture Index"]).all()
        assert len(sol.model.fault_sections_with_solution_slip_rates) == len(sol.solution_file.fault_sections)
        assert sol.model.fault_sections_with_solution_slip_rates.loc[0, "Solution Slip Rate"] == approx(
            0.02632348565225584, abs=1e-10, rel=1e-6
        )

    def test_target_slip_rates(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        assert "Target Slip Rate" in sol.solution_file.fault_sections.columns
        assert "Target Slip Rate StdDev" in sol.solution_file.fault_sections.columns
        assert "SlipRate" not in sol.solution_file.fault_sections.columns
        assert "SlipRateStdDev" not in sol.solution_file.fault_sections.columns
        assert "Section Index" not in sol.solution_file.fault_sections.columns

    def test_section_target_slip_rates(self, crustal_solution_fixture):
        sol = crustal_solution_fixture
        tss = sol.solution_file.section_target_slip_rates
        assert tss is not None
        assert tss.shape == sol.solution_file.section_target_slip_rates.shape

    def test_crustal_filter_solution(self, crustal_solution_fixture):
        sol = crustal_solution_fixture

        # take the first 5 ruptures and build a new solution
        new_sol = InversionSolution.filter_solution(sol, sol.solution_file.ruptures.head(20)["Rupture Index"])
        assert isinstance(new_sol, InversionSolution)
        print(new_sol.solution_file.rupture_rates)
        print(sol.solution_file.rupture_rates)
        assert sol.solution_file.rupture_rates.head(20).all().all() == new_sol.solution_file.rupture_rates.all().all()

    @pytest.mark.skip('placeholder for a future ticket')
    def test_crustal_filter_solution_trimmed(self, crustal_solution_fixture):
        # a trimmed sdolution has all the extra solution data (geojson etc) trimmed to match the ruptures changes,
        #  let's list them here

        sol = crustal_solution_fixture

        # take the first N ruptures and build a new solution
        N = 10
        new_sol = InversionSolution.filter_solution(sol, sol.solution_file.ruptures.head(N)["Rupture Index"])
        assert isinstance(new_sol, InversionSolution)
        print(new_sol.solution_file.rupture_rates)
        print(sol.solution_file.rupture_rates)
        assert sol.solution_file.rupture_rates.head(N).all().all() == new_sol.solution_file.rupture_rates.all().all()


class TestSmallPuyInversionSolution(object):

    def test_new_puysegur_filter_solution(self, puysegur_small_fixture):
        sol = puysegur_small_fixture

        # take the first 5 ruptures and build a new solution
        new_sol = InversionSolution.filter_solution(sol, sol.solution_file.ruptures.head()["Rupture Index"])
        assert isinstance(new_sol, InversionSolution)
        print(new_sol.solution_file.rupture_rates)
        print(sol.solution_file.rupture_rates)
        assert sol.solution_file.rupture_rates.head().all().all() == new_sol.solution_file.rupture_rates.all().all()

    def test_check_indexes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert sol.solution_file.rupture_rates.index == sol.solution_file.rupture_rates["Rupture Index"]
        assert sol.solution_file.ruptures.index == sol.solution_file.ruptures["Rupture Index"]
        assert sol.solution_file.indices.index.all() == sol.solution_file.indices["Rupture Index"].all()
        # assert sol.rupture_rates["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        # assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_shapes(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        print(sol.solution_file.rupture_rates)
        assert sol.solution_file.rupture_rates.shape == (10, 2)
        print(sol.solution_file.indices)
        assert sol.solution_file.indices.shape == (10, 273)
        print(sol.solution_file.ruptures)
        assert sol.solution_file.ruptures.shape == (10, 5)

    def test_fault_regime(self, puysegur_small_fixture):
        sol = puysegur_small_fixture
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'
