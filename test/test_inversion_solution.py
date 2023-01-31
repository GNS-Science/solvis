#!python3 test_inversion_solution.py

import os
import pathlib
import unittest

from solvis import InversionSolution


class TestInversionSolution(unittest.TestCase):
    def test_load_crustal_from_archive(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(str(filename))
        assert isinstance(sol, InversionSolution)

    def test_load_subduction_from_archive(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))
        assert isinstance(sol, InversionSolution)
