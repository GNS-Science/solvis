import os
import pathlib
import unittest

import geopandas as gpd
import numpy as np
import pyvista as pv
from nzshm_common.location.location import location_by_id
from pyproj import Transformer

from solvis import InversionSolution


class TestPyvistaDistances(unittest.TestCase):
    def test_basic_0_rake_90(self):

        mesh0 = pv.PolyData([0, 0, 0])

        p0 = [0, 1, 0]  # 1st top-trace point
        p1 = [0, 2, 0]  # 2nd top-trace point
        p2 = [1, 1, 10]  # 1st botton trace point
        p3 = [1, 2, 10]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3])
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 1

    def test_basic_1_further_at_depth(self):
        mesh0 = pv.PolyData([0, 0, 0])

        p0 = [0, 2, 0]  # 1st top-trace point
        p1 = [0, 3, 0]  # 2nd top-trace point
        p2 = [2, 2, 10]  # 1st botton trace point
        p3 = [2, 3, 10]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3])
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [0]
        assert d_exact[0] == 2.0

    def test_basic_2_closer_at_depth(self):
        mesh0 = pv.PolyData([0, 0, 0])

        p0 = [10, 2, 0]  # 1st top-trace point
        p1 = [10, 3, 0]  # 2nd top-trace point
        p2 = [0, 2, 5]  # 1st botton trace point
        p3 = [0, 3, 5]  # 2nd bottom trace point

        mesh1 = pv.PolyData([p0, p1, p2, p3])
        closest_cells, closest_points = mesh1.find_closest_cell(mesh0.points, return_closest_point=True)
        d_exact = np.linalg.norm(mesh0.points - closest_points, axis=1)

        print(closest_cells)
        # print(closest_points)
        print(d_exact)
        assert closest_cells == [2]
        assert d_exact[0] > 5


class TestPyvistaDistanceIntegration(unittest.TestCase):
    def test_calc_distance_to_a_fault_section(self):

        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))

        q0 = gpd.GeoDataFrame(sol.fault_sections)

        SECTION_IDX = 43
        print(q0.geometry[SECTION_IDX], q0.UpDepth[SECTION_IDX], q0.LowDepth[SECTION_IDX])

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']
        print(f'datum: {WLG}')
        origin = pv.PolyData([0, 0, 0])

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        print(f'trace coords: {q0.geometry[SECTION_IDX].coords.xy}')
        trace = transformer.transform(*q0.geometry[SECTION_IDX].coords.xy)
        print(f'trace offsets: {trace} (in metres relative to datum)')

        # TODO calculate lower trace lat & lon based on dip_direction
        surface = pv.PolyData(
            [
                [trace[0][0], trace[1][0], int(q0.UpDepth[SECTION_IDX] * 1000)],  # OK
                [trace[0][1], trace[1][1], int(q0.UpDepth[SECTION_IDX] * 1000)],  # OK
                [trace[0][0], trace[1][0], int(q0.LowDepth[SECTION_IDX] * 1000)],  # nope, but ok for basic test
                [trace[0][1], trace[1][1], int(q0.LowDepth[SECTION_IDX] * 1000)],  # nope
            ]
        )

        closest_cells, closest_points = surface.find_closest_cell(origin.points, return_closest_point=True)
        d_exact = np.linalg.norm(origin.points - closest_points, axis=1)

        print(closest_cells)
        print(d_exact)
        assert d_exact[0] <= 50000
        # assert 0
