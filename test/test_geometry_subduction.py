#! python test_geometry

import os
import pathlib
import unittest
from copy import deepcopy

from shapely import get_coordinates
from shapely.geometry import LineString, Point

import solvis
from solvis.geometry import bearing, dip_direction


class TestSubductionSurface(unittest.TestCase):
    def setUp(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        self.solution = solvis.InversionSolution().from_archive(filename)
        self.fault_sections = deepcopy(self.solution.fault_sections)

    @unittest.skip('use to write out some files')
    def test_write_surface_geojson(self):
        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        original_archive = pathlib.PurePath(  # noqa
            folder, "fixtures/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTQz.zip"
        )
        # solution = solvis.InversionSolution().from_archive(original_archive)
        # solvis.export_geojson(solution.fault_surfaces(), "surfaces_original.json" )
        # solvis.export_geojson(solution.fault_surfaces(refine_dip_dir=True), "surfaces_refined.json" )

        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        solution = solvis.InversionSolution().from_archive(str(filename))
        solvis.export_geojson(solution.fault_surfaces(), "surfaces_hikurangi.json")

        filename = pathlib.PurePath(folder, "fixtures/PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip")
        solution = solvis.InversionSolution().from_archive(str(filename))
        solvis.export_geojson(solution.fault_surfaces(), "surfaces_puysegur.json")

    def test_tile_0_dipdir(self):
        tile_0 = [section for i, section in self.fault_sections.iterrows()][0]

        print('tile_0', tile_0)

        flat_geom = LineString(get_coordinates(tile_0.geometry))

        print(flat_geom)

        point_a = Point(reversed(flat_geom.coords[0]))
        point_b = Point(reversed(flat_geom.coords[-1]))

        print(point_a, point_b)
        print(f"bearing {bearing(point_a, point_b)}")

        this_dd = dip_direction(point_a, point_b)
        print(f"dip_dir {dip_direction(point_a, point_b)}")

        self.assertAlmostEqual(this_dd, 322, 0)
