#!python3 test_inversion_solution.py

import os
import pathlib
import unittest

from solvis import InversionSolution


class TestInversionSolution(unittest.TestCase):
    def test_load_from_archive(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(str(filename))
        assert isinstance(sol, InversionSolution)
