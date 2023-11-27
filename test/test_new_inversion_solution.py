#!python3 test_new_inversion_solution.py

import os
import pathlib
import tempfile
import unittest

import solvis


def setUpModule():
    global temp_dir
    temp_dir = tempfile.TemporaryDirectory()

    print('gettempdir():', tempfile.gettempdir())
    print('gettempprefix():', tempfile.gettempprefix())


def tearDownModule():
    pass


class TestNewInversionSolutionSubduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        cls.original_archive = pathlib.PurePath(
            folder, "fixtures", "AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )

        global temp_dir
        cls.temp_dir = temp_dir
        cls.original_solution = solvis.InversionSolution().from_archive(str(cls.original_archive))

    def test_rupt_ids_above_rate(self):

        sol = TestNewInversionSolutionSubduction.original_solution
        ruptures_all = solvis.rupt_ids_above_rate(sol, 0)
        ruptures_small = solvis.rupt_ids_above_rate(sol, 1e-15)
        ruptures_med = solvis.rupt_ids_above_rate(sol, 1e-10)
        ruptures_big = solvis.rupt_ids_above_rate(sol, 1e-6)

        self.assertEqual(ruptures_all, sol.ruptures.shape[0])
        self.assertLess(len(ruptures_small), len(ruptures_all))
        self.assertLess(len(ruptures_med), len(ruptures_small))
        self.assertLess(len(ruptures_big), len(ruptures_med))

    def test_filter_solution_ruptures(self):
        sol = TestNewInversionSolutionSubduction.original_solution
        ruptures_big = solvis.rupt_ids_above_rate(sol, 1e-6)

        new_sol = solvis.InversionSolution.filter_solution(sol, ruptures_big)
        self.assertEqual(ruptures_big.shape[0], new_sol.ruptures.shape[0])


class TestNewInversionSolutionCrustal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        cls.original_archive = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")

        global temp_dir
        cls.temp_dir = temp_dir
        cls.original_solution = solvis.InversionSolution.from_archive(str(cls.original_archive))

    def test_rupt_ids_above_rate(self):

        sol = TestNewInversionSolutionCrustal.original_solution
        ruptures_all = solvis.rupt_ids_above_rate(sol, 0)
        ruptures_small = solvis.rupt_ids_above_rate(sol, 1e-15)
        ruptures_med = solvis.rupt_ids_above_rate(sol, 1e-10)
        ruptures_big = solvis.rupt_ids_above_rate(sol, 1e-6)

        self.assertEqual(ruptures_all, sol.ruptures.shape[0])
        self.assertLess(len(ruptures_small), len(ruptures_all))
        self.assertLess(len(ruptures_med), len(ruptures_small))
        self.assertLess(len(ruptures_big), len(ruptures_med))

    def test_filter_updates_rupture_attr(self):

        sol = TestNewInversionSolutionCrustal.original_solution

        ruptures = solvis.rupt_ids_above_rate(sol, 1e-5)
        new_sol = solvis.InversionSolution.filter_solution(sol, ruptures)

        self.assertEqual(new_sol.ruptures.shape[0], len(ruptures))
        self.assertEqual(new_sol.ruptures['Rupture Index'].to_list(), ruptures)

        self.assertNotEqual(sol.ruptures.shape, new_sol.ruptures.shape)
        self.assertNotEqual(sol.rupture_rates.shape, new_sol.rupture_rates.shape)

    def test_filter_writes_attribs_non_compatible_mode(self):
        """
        With non-compatible mode redundant rows can be removed but the rupture indices are as original.
        This is not compatible with opensha which expects sequential 0-based indexing.
        """

        sol = TestNewInversionSolutionCrustal.original_solution

        ruptures = solvis.rupt_ids_above_rate(sol, 1e-6)
        new_sol = solvis.InversionSolution.filter_solution(sol, ruptures)

        folder = str(TestNewInversionSolutionCrustal.temp_dir.name)
        new_path = pathlib.Path(folder, 'test_non_compatible_archive.zip')

        new_sol.to_archive(str(new_path), TestNewInversionSolutionCrustal.original_archive, compat=False)
        read_sol = solvis.InversionSolution.from_archive(new_path)

        self.assertEqual(read_sol.indices.shape[0], len(ruptures))
        self.assertEqual(read_sol.rupture_rates.shape[0], len(ruptures))
        self.assertEqual(read_sol.ruptures.shape[0], len(ruptures))

    def test_filter_writes_attribs_compatible_mode(self):
        """
        With compatible mode all the dataframes should be reindexed from 0
        """

        sol = TestNewInversionSolutionCrustal.original_solution

        ruptures = solvis.rupt_ids_above_rate(sol, 1e-6)
        new_sol = solvis.InversionSolution.filter_solution(sol, ruptures)

        folder = str(TestNewInversionSolutionCrustal.temp_dir.name)
        new_path = pathlib.Path(folder, 'test_compatible_archive.zip')

        new_sol.to_archive(str(new_path), TestNewInversionSolutionCrustal.original_archive, compat=True)

        read_sol = solvis.InversionSolution.from_archive(new_path)

        self.assertEqual(read_sol.indices.shape[0], len(ruptures))
        self.assertEqual(read_sol.rupture_rates.shape[0], len(ruptures))
        self.assertEqual(read_sol.ruptures.shape[0], len(ruptures))
