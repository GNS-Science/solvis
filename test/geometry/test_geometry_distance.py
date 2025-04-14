import json
import os
import pathlib
import unittest

import geopandas as gpd
import numpy as np
import pytest
from nzshm_common.location.location import location_by_id
from pyproj import Transformer
from pytest import approx

from solvis import InversionSolution, geojson, geometry

pyvista = pytest.importorskip("pyvista")

TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent


@pytest.fixture(scope="session")
def small_crustal_solution():
    original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
    yield InversionSolution().from_archive(original_archive)


class TestPyvistaDistances(unittest.TestCase):
    def test_basic_0_rake_90(self):

        mesh0 = pyvista.PolyData([[0, 0, 0]], force_float=False)

        p0 = [0, 1, 0]  # 1st top-trace point
        p1 = [0, 2, 0]  # 2nd top-trace point
        p2 = [1, 1, 10]  # 1st botton trace point
        p3 = [1, 2, 10]  # 2nd bottom trace point

        mesh1 = pyvista.PolyData([p0, p1, p2, p3], force_float=False)
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 1

    def test_basic_1_further_at_depth(self):
        mesh0 = pyvista.PolyData([0, 0, 0], force_float=False)

        p0 = [0, 2, 0]  # 1st top-trace point
        p1 = [0, 3, 0]  # 2nd top-trace point
        p2 = [2, 2, 10]  # 1st botton trace point
        p3 = [2, 3, 10]  # 2nd bottom trace point

        mesh1 = pyvista.PolyData([p0, p1, p2, p3], force_float=False)

        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 2.0

    def test_basic_2_closer_at_depth(self):
        mesh0 = pyvista.PolyData([0, 0, 0], force_float=False)

        p0 = [10, 2, 0]  # 1st top-trace point
        p1 = [10, 3, 0]  # 2nd top-trace point
        p2 = [0, 2, 5]  # 1st botton trace point
        p3 = [0, 3, 5]  # 2nd bottom trace point

        mesh1 = pyvista.PolyData([p0, p1, p2, p3], force_float=False)
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [2]
        assert d_exact[0] > 5

    def test_calc_distance_345_line(self):
        origin = pyvista.PolyData([0, 0, 0], force_float=False)
        surface = pyvista.PolyData([[3, 0, 4], [3, 1, 4]], force_float=False)

        closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
        d_exact = np.linalg.norm(origin.points - closest_points, axis=1)

        print(closest_cells)
        print(d_exact)
        assert d_exact[0] == 5

    def test_calc_distance_345_surface(self):
        origin = pyvista.PolyData([0, 0, 0], force_float=False)
        surface = pyvista.PolyData([[3, 0, 4], [15, 0, 4], [15, 1, 10], [3, 1, 10]], force_float=False)
        closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
        d_exact = np.linalg.norm(origin.points - closest_points, axis=1)

        print(closest_cells)
        print(d_exact)
        assert d_exact[0] == 5


class TestSurfaceDistanceCalculation(object):

    @pytest.mark.skip('until 3d distance is figured out - currently dip angle is not considered.')
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

        new_series = gdf.apply(
            lambda section: geometry.section_distance(
                transformer, section.geometry, section.DipDir, section.DipDeg, section.UpDepth, section.LowDepth
            ),
            axis=1,
        )
        assert new_series.min() == approx(25067.57 / 1e3)

    @pytest.mark.skip('until 3d distance is figured out - currently dip angle is not considered.')
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
            lambda section: geometry.section_distance(
                transformer, section.geometry, section.DipDir, section.DipDeg, section.UpDepth, section.LowDepth
            ),
            axis=1,
        )
        # print ( new_series.loc[lambda x: x <= 100000 ])
        assert new_series.min() == approx(38282.218 / 1e3)

    @pytest.mark.skip('until 3d distance is figured out - currently dip angle is not considered.')
    @pytest.mark.parametrize('dist_km', [10, 20, 50, 70, 100, 150, 160, 180])
    # @pytest.mark.parametrize('dist_km', [30, 160])
    def test_calc_crustal_compare_algorithms(self, dist_km, small_crustal_solution):
        sol = small_crustal_solution
        # # set up WLG as our datum
        WLG_CODE = 'WLG'
        WLG = location_by_id(WLG_CODE)
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        polygon = geometry.circle_polygon(radius_m=dist_km * 1000, lon=WLG['longitude'], lat=WLG['latitude'])
        polygon_intersect_df = gdf[gdf['geometry'].intersects(polygon)]  # whitemans_0)]
        print(polygon_intersect_df)

        gdf['distance_km'] = gdf.apply(
            lambda section: geometry.section_distance(transformer, section.geometry, section.UpDepth, section.LowDepth),
            axis=1,
        )
        print(polygon_intersect_df['FaultID'])
        print(gdf[gdf['distance_km'] <= dist_km]['FaultID'])

        assert list(polygon_intersect_df['FaultID']) == list(gdf[gdf['distance_km'] <= dist_km]['FaultID'])

    @pytest.mark.skip('until 3d distance is figured out - currently dip angle is not considered.')
    @pytest.mark.parametrize('dist_km', [200, 300, 500, 1000])
    def test_calc_crustal_compare_algorithms_larger_distance(self, dist_km):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)

        # # set up WLG as our datum
        WLG_CODE = 'WLG'
        WLG = location_by_id(WLG_CODE)
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        gdf = gpd.GeoDataFrame(sol.fault_surfaces())
        # gdf = gdf[gdf.FaultID.isin([64, 65])]

        polygon = geometry.circle_polygon(radius_m=dist_km * 1000, lon=WLG['longitude'], lat=WLG['latitude'])
        polygon_intersect_df = gdf[gdf['geometry'].intersects(polygon)]  # whitemans_0)]

        print('gdf columns')
        print("===========")
        print(gdf.columns)
        print()
        print("circle_polygon result info()")
        print('============================')
        print(polygon_intersect_df.info())
        print()

        gdf2 = sol.solution_file.fault_sections
        # gdf2 = gdf2[gdf2.FaultID.isin([64, 65])]
        gdf2['distance_km'] = gdf2.apply(
            lambda section: geometry.section_distance(
                transformer, section.geometry, section.DipDir, section.DipDeg, section.UpDepth, section.LowDepth
            ),
            axis=1,
        )

        print("circle_polygon result")
        print('=======================')
        print(polygon_intersect_df)
        print()
        print("section_distance result")
        print('=======================')
        print(gdf2)  # gdf['distance_km'] <= dist_km])
        print()
        if list(polygon_intersect_df['FaultID']) != list(gdf2[gdf2['distance_km'] <= dist_km]['FaultID']):
            # we need some visual diagnostics
            inspect_ids = set(list(polygon_intersect_df['FaultID'])).symmetric_difference(
                set(gdf2[gdf2['distance_km'] <= dist_km]['FaultID'])
            )
            folder = pathlib.Path(__name__).parent
            print(polygon)

            poly_geojson = geojson.location_features_geojson([WLG_CODE], dist_km)
            # print(poly_geojson)
            json.dump(poly_geojson, open(folder / "polygon.geojson", 'w'), indent=2)

            poly_faults_df = polygon_intersect_df[polygon_intersect_df['FaultID'].isin(inspect_ids)]
            poly_faults_df.to_file(str(folder / "polygon_faults.geojson"), driver='GeoJSON')

            fids = gdf2[gdf2['distance_km'] <= dist_km]["FaultID"].tolist()
            sdf = sol.fault_surfaces()
            distance_faults_df = sdf[sdf['FaultID'].isin(fids)]
            distance_faults_df.to_file(str(folder / "distance_faults.geojson"), driver='GeoJSON')
            assert 0


def test_build_surface(small_crustal_solution):

    sol = small_crustal_solution
    gdf = sol.solution_file.fault_sections
    gdf = gdf[gdf.FaultID.isin([64])]

    fault_section = gdf.iloc[0]
    print(fault_section.geometry)
    print()
    print(fault_section.geometry.coords.xy)

    sfc = geometry.build_surface(
        fault_section.geometry,
        fault_section.DipDir,
        fault_section.DipDeg,
        fault_section.UpDepth,
        fault_section.LowDepth,
        with_z_dimension=True,
    )
    print(sfc)
