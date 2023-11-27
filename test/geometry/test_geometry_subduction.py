#! python test_geometry

import os
import pathlib
import unittest
from copy import deepcopy
from datetime import datetime as dt

import pytest
from shapely import get_coordinates
from shapely.geometry import LineString, Point

import solvis
from solvis.geometry import bearing, dip_direction

# "fixtures/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTQz.zip"
CRU_ARCHIVE = "fixtures/ModularAlpineVernonInversionSolution.zip"
HIK_ARCHIVE = "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
PUY_ARCHIVE = "fixtures/PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip"


TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent


class TestSubductionSurface(unittest.TestCase):
    def setUp(self):

        filename = pathlib.PurePath(TEST_FOLDER, HIK_ARCHIVE)
        self.solution = solvis.InversionSolution().from_archive(filename)
        self.fault_sections = deepcopy(self.solution.fault_sections)

    @unittest.skip('use to write out some files')
    def test_write_surface_geojson(self):
        original_archive = pathlib.PurePath(TEST_FOLDER, CRU_ARCHIVE)  # noqa
        # solution = solvis.InversionSolution().from_archive(original_archive)
        # solvis.export_geojson(solution.fault_surfaces(), "surfaces_original.json" )
        # solvis.export_geojson(solution.fault_surfaces(refine_dip_dir=True), "surfaces_refined.json" )

        filename = pathlib.PurePath(TEST_FOLDER, HIK_ARCHIVE)
        solution = solvis.InversionSolution().from_archive(str(filename))
        solvis.rupt_ids_above_rate(1e-8)
        solvis.export_geojson(solution.fault_surfaces(), "surfaces_hikurangi.json")

        filename = pathlib.PurePath(TEST_FOLDER, PUY_ARCHIVE)
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

    def test_subduction_rupture_surface(self):
        filename = pathlib.PurePath(TEST_FOLDER, PUY_ARCHIVE)
        solution = solvis.InversionSolution().from_archive(str(filename))
        surface = solution.rupture_surface(4)
        assert surface.shape == (8, 22)

    @pytest.mark.slow
    def test_crustal_rupture_surface(self):
        filename = pathlib.PurePath(TEST_FOLDER, CRU_ARCHIVE)
        solution = solvis.InversionSolution().from_archive(str(filename))

        rupture_id = 101
        surface = solution.rupture_surface(rupture_id)

        print(surface)
        assert surface.shape == (25, 22)
        # solvis.export_geojson(surface, f"surfaces_crustal_rupt-{rupture_id}.geojson")

    @pytest.mark.slow
    def test_rate_caching_crustal_rupture_surface(self):
        filename = pathlib.PurePath(TEST_FOLDER, CRU_ARCHIVE)
        solution = solvis.InversionSolution().from_archive(str(filename))

        rupture_id = 101
        t0 = dt.utcnow()
        solution.rupture_surface(rupture_id)
        uncached_time = dt.utcnow() - t0

        t1 = dt.utcnow()
        solution.rupture_surface(rupture_id)
        cached_time = dt.utcnow() - t1

        print(cached_time, uncached_time)
        assert cached_time < uncached_time
        assert cached_time.microseconds < 1e5

    @unittest.skip('WIP filtered rutpures geojson')
    def test_write_filtered_geojson(self):
        filename = pathlib.PurePath(TEST_FOLDER, PUY_ARCHIVE)
        solution = solvis.InversionSolution().from_archive(str(filename))
        rate = 5e-5
        ri = solvis.rupt_ids_above_rate(solution, rate)
        print(f'rate: {rate} count: {len(ri)}')

        ri_sol = solvis.new_sol(solution, ri)
        print("rs_with_rupture_rates shape", ri_sol.rs_with_rupture_rates.shape)
        print("sections shape", ri_sol.rupture_sections.shape)
        solvis.export_geojson(ri_sol.fault_surfaces(), f"surfaces_puysegur_above-{rate}.geojson", indent=2)
        assert 0
