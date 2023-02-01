#!python3 test_inversion_solution.py

import os
import pathlib
import unittest

from nzshm_common.location.location import location_by_id

from solvis import InversionSolution, circle_polygon


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

    def test_ruptures_intersecting_crustal(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(str(filename))

        WLG = location_by_id('WLG')
        # polygon = circle_polygon(5e5, -38.662334, 178.017654)
        polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 00km circle around WLG

        ruptures = sol.get_ruptures_intersecting(polygon)
        all_rupture_ids = list(sol.ruptures.index)

        self.assertTrue(len(sol.ruptures) > len(ruptures))
        self.assertTrue(set(all_rupture_ids).issuperset(set(ruptures)))
