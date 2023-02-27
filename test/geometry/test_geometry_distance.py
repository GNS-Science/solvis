import os
import pathlib
import unittest

import geopandas as gpd
import numpy as np
import pytest
import pyvista as pv
from nzshm_common.location.location import location_by_id
from pyproj import Transformer
from pytest import approx

from solvis import InversionSolution, geometry

TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent


class TestPyvistaDistances(unittest.TestCase):
    def test_basic_0_rake_90(self):

        mesh0 = pv.PolyData([0, 0, 0], force_float=False)

        p0 = [0, 1, 0]  # 1st top-trace point
        p1 = [0, 2, 0]  # 2nd top-trace point
        p2 = [1, 1, 10]  # 1st botton trace point
        p3 = [1, 2, 10]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3], force_float=False)
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


class TestSurfaceDistanceCalculation(object):
    def test_calc_distance_to_a_subduction_fault_section(self):

        filename = pathlib.PurePath(
            TEST_FOLDER, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        print(gdf)

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
        new_series = gdf.apply(
            lambda section: geometry.section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth),
            axis=1,
        )
        assert new_series.min() == approx(25067.57 / 1e3)

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

        new_series = gdf.apply(
            lambda section: geometry.section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth),
            axis=1,
        )
        # print ( new_series.loc[lambda x: x <= 100000 ])
        assert new_series.min() == approx(38282.218 / 1e3)

    @pytest.mark.parametrize('dist_km', [10, 20, 30, 50, 70, 100, 150, 180])
    def test_calc_crustal_compare_algorithms(self, dist_km):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        polygon = geometry.circle_polygon(radius_m=dist_km * 1000, lon=WLG['longitude'], lat=WLG['latitude'])
        polygon_intersect_df = gdf[gdf['geometry'].intersects(polygon)]  # whitemans_0)]
        print(polygon_intersect_df.info())

        gdf['distance_km'] = gdf.apply(
            lambda section: geometry.section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth),
            axis=1,
        )

        print(polygon_intersect_df['FaultID'])

        print(gdf[gdf['distance_km'] <= dist_km]['FaultID'])

        assert list(polygon_intersect_df['FaultID']) == list(gdf[gdf['distance_km'] <= dist_km]['FaultID'])

    @pytest.mark.parametrize('dist_km', [200, 300, 500, 1000])
    def test_calc_crustal_compare_algorithms_larger_distance(self, dist_km):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        polygon = geometry.circle_polygon(radius_m=dist_km * 1000, lon=WLG['longitude'], lat=WLG['latitude'])
        polygon_intersect_df = gdf[gdf['geometry'].intersects(polygon)]  # whitemans_0)]
        print(polygon_intersect_df.info())

        gdf['distance_km'] = gdf.apply(
            lambda section: geometry.section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth),
            axis=1,
        )

        distance_ids = set(gdf[gdf['distance_km'] <= dist_km]['FaultID'])
        intersects_ids = set(polygon_intersect_df['FaultID'])

        diffs = distance_ids.difference(intersects_ids)

        assert diffs == set([])  # should be an empty set
        print(diffs)
        print(distance_ids)
        print(gdf[gdf['FaultID'].isin(list(diffs))])

        # with open(f'surface_within_{dist_km}_of_wellington.geojson', 'w') as fo:
        #     fo.write(gdf[gdf['distance_km'] <= dist_km].to_json(indent=2))
        #     fo.close()
        # assert 0
