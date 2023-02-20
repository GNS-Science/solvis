import os
import pathlib
import unittest
import timeit

import geopandas as gpd
import numpy as np
import pyvista as pv
from nzshm_common.location.location import location_by_id
from pyproj import Transformer

from solvis import InversionSolution
from pytest import approx, mark


TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent

class TestPyvistaDistances(unittest.TestCase):
    def test_basic_0_rake_90(self):

        mesh0 = pv.PolyData([0, 0, 0], force_float=False)

        p0 = [0, 1, 0]  # 1st top-trace point
        p1 = [0, 2, 0]  # 2nd top-trace point
        p2 = [1, 1, 10]  # 1st botton trace point
        p3 = [1, 2, 10]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3],  force_float=False)
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 1

    def test_basic_1_further_at_depth(self):
        mesh0 = pv.PolyData([0, 0, 0], force_float=False)

        p0 = [0, 2, 0]  # 1st top-trace point
        p1 = [0, 3, 0]  # 2nd top-trace point
        p2 = [2, 2, 10]  # 1st botton trace point
        p3 = [2, 3, 10]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3], force_float=False)

        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 2.0

    def test_basic_2_closer_at_depth(self):
        mesh0 = pv.PolyData([0, 0, 0], force_float=False)


        p0 = [10, 2, 0]  # 1st top-trace point
        p1 = [10, 3, 0]  # 2nd top-trace point
        p2 = [0, 2, 5]  # 1st botton trace point
        p3 = [0, 3, 5]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3], force_float=False)
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [2]
        assert d_exact[0] > 5

    def test_calc_distance_345_line(self):
        origin = pv.PolyData([0, 0, 0], force_float=False)
        surface = pv.PolyData([[3, 0, 4], [3, 1, 4]], force_float=False)

        closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
        d_exact = np.linalg.norm(origin.points - closest_points, axis=1)

        print(closest_cells)
        print(d_exact)
        assert d_exact[0] == 5

    def test_calc_distance_345_surface(self):
        origin = pv.PolyData([0, 0, 0], force_float=False)
        surface = pv.PolyData([[3, 0, 4], [15, 0, 4], [15, 1, 10], [3, 1, 10]], force_float=False)
        closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
        d_exact = np.linalg.norm(origin.points - closest_points, axis=1)

        print(closest_cells)
        print(d_exact)
        assert d_exact[0] == 5

def section_distance(transformer, geometry, upper_depth, lower_depth):
    # print(f'trace coords: {geometry.exterior.coords.xy}')
    trace = transformer.transform(*geometry.exterior.coords.xy)
    # print(f'trace offsets: {trace} (in metres relative to datum)')
    origin = pv.PolyData([0.0, 0.0, 0.0]) #, force_float=False)
    surface = pv.PolyData(
        [
            [float(trace[0][0]), float(trace[1][0]), float(upper_depth * 1000)],  # OK
            [float(trace[0][1]), float(trace[1][1]), float(upper_depth * 1000)],  # OK
            [float(trace[0][0]), float(trace[1][0]), float(lower_depth * 1000)],  # nope, but ok for basic test
            [float(trace[0][1]), float(trace[1][1]), float(lower_depth * 1000)],  # nope
        ]
    )

    closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
    d_exact = np.linalg.norm(origin.points - closest_points, axis=1)
    return d_exact[0]


class TestSurfaceDistanceCalculation(unittest.TestCase):

    def test_calc_distance_to_a_subduction_fault_section(self):

        filename = pathlib.PurePath(
            TEST_FOLDER, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
        new_series = gdf.apply(lambda section: section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth), axis=1)
        assert new_series.min() == approx(25067.57)

    def test_calc_distance_to_a_crustal_fault_section(self):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        new_series = gdf.apply(lambda section: section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth), axis=1)
        # print ( new_series.loc[lambda x: x <= 100000 ])
        assert new_series.min() == approx(38282.218)

    @mark.slow
    def test_calc_performance_to_a_crustal_fault_section(self):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)

        #pick a rupture section
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        # time it takes to execute the main statement a number of times, measured in seconds as a float.
        count = 10
        elapsed = timeit.timeit(lambda: gdf.apply(lambda section: section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth), axis=1),
            number = count
        )/10
        assert elapsed < 0.05 # 50msec

    @mark.slow
    def test_calc_peformance_to_a_subduction_fault_section(self):

        filename = pathlib.PurePath(
            TEST_FOLDER, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        new_series = gdf.apply(lambda section: section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth), axis=1)
        count = 10
        elapsed = timeit.timeit(lambda: gdf.apply(lambda section: section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth), axis=1),
            number = count
        )/10
        assert elapsed < 0.2 # 200msec

