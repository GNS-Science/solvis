#!python3 test_inversion_solution.py

import os
import pathlib
import unittest

from solvis import InversionSolution

# from solvis.inversion_solution.solution_surfaces_builder import SolutionSurfacesBuilder


class SolutionLike:
    def __init__(self, fault_regime, fault_sections, fault_sections_with_rupture_rates):
        self.fault_regime = fault_regime
        self.fault_sections = fault_sections
        self.fault_sections_with_rupture_rates = fault_sections_with_rupture_rates


class TestSolutionSurfacesBuilder(unittest.TestCase):
    def test_build_crustal_from_archive(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution.from_archive(str(filename))
        likeness = SolutionLike(sol.fault_regime, sol.fault_sections, sol.fault_sections_with_rupture_rates)

        # assert isinstance(likeness, InversionSolution)
        assert likeness.fault_regime == 'CRUSTAL'

        fs_gdf = sol.fault_surfaces()
        fsr_gdf = sol.rupture_surface(0)
        assert fs_gdf.shape == (86, 14)
        assert fsr_gdf.shape == (2, 22)
        # print(fsr_gdf.columns)
        # assert 0

    def test_build_subduction_from_archive(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))
        assert isinstance(sol, InversionSolution)
        assert sol.fault_regime == 'SUBDUCTION'

        fs_gdf = sol.fault_surfaces()
        fsr_gdf = sol.rupture_surface(0)

        # No DipDir column in subduction solutions
        assert fs_gdf.shape == (452, 13)
        assert fsr_gdf.shape == (2, 21)
        # print(fsr_gdf.columns)
        # assert 0
