import math
import os
import pathlib
import unittest

import Geometry3D as g3d
import geopandas as gpd
from nzshm_common.location.location import location_by_id
from pyproj import Transformer

from solvis import InversionSolution


class TestGeometry3DDistances(unittest.TestCase):
    def test_basic_0(self):
        p0 = g3d.Point(1, 1, 0)  # 1st top-trace point
        p1 = g3d.Point(1, 10, 0)  # 2nd top-trace point
        p2 = g3d.Point(1, 1, 10)  # point at new depth
        plane = g3d.Plane(p0, p1, p2)
        self.assertEqual(plane.distance(g3d.origin()), 1.0)

    def test_basic_1(self):
        p0 = g3d.Point(10, 1, 0)  # 1st top-trace point
        p1 = g3d.Point(10, 10, 0)  # 2nd top-trace point
        p2 = g3d.Point(10, 1, 10)  # point at new depth
        plane = g3d.Plane(p0, p1, p2)
        self.assertEqual(plane.distance(g3d.origin()), 10.0)

    def test_basic_2(self):
        p0 = g3d.Point(10, 1, 0)  # 1st top-trace point
        p1 = g3d.Point(10, 10, 0)  # 2nd top-trace point
        p2 = g3d.Point(5, 1, 10)  # closer at depth
        plane = g3d.Plane(p0, p1, p2)
        assert plane.distance(g3d.origin()) < 10.0

    @unittest.skip('this shows us it ain\'t gonna work using a plane')
    def test_basic_3(self):
        p0 = g3d.Point(10, 1, 0)  # 1st top-trace point
        p1 = g3d.Point(10, 10, 0)  # 2nd top-trace point
        p2 = g3d.Point(15, 1, 10)  # further at depth = closer above ground == no good
        plane = g3d.Plane(p0, p1, p2)
        assert plane.distance(g3d.origin()) > 10.0

    @unittest.skip('this does\'t help/work')
    def test_can_we_get_intersection_of_rect_and_plane(self):
        p0 = g3d.Point(10, 1, 0)  # 1st top-trace point
        p1 = g3d.Point(10, 10, 0)  # 2nd top-trace point
        p2 = g3d.Point(10.000333, 1, 10)  # further at depth = closer above ground == no good

        plane = g3d.Plane(p0, p1, p2)
        rect = g3d.Parallelogram(p0, g3d.Vector(p0, p1), g3d.Vector(p0, p2))

        plane_rect = plane.intersection(rect)
        print(plane_rect)

        print(plane.distance(g3d.origin()))
        print(g3d.origin().distance(plane))
        assert 0


wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"


class TestSphericalIntersections(unittest.TestCase):
    def test_build_a_sphere_with_radius(self):

        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']
        radius_m = 10000  # 10km

        # convert to azimuthal metres relative to our location WLG ...

        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
        datum = transformer.transform(lon, lat)

        print(datum)

        sphere = g3d.Sphere(g3d.Point(0, 0, 0), radius_m)  # , n1=50, n2=20)

        print(sphere)

    @unittest.skip('this does\'t help/work')
    def test_build_a_plane_from_a_fault_section(self):

        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        filename = pathlib.PurePath(
            folder, "fixtures/AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
        )
        sol = InversionSolution().from_archive(str(filename))

        q0 = gpd.GeoDataFrame(sol.fault_sections)

        SECTION_IDX = 30
        print(q0.geometry[SECTION_IDX], q0.UpDepth[SECTION_IDX], q0.LowDepth[SECTION_IDX])
        # print(dir(q0.geometry[SECTION_IDX]))

        print(f'section info {q0.columns}')

        # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']
        print(f'datum: {WLG}')

        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
        datum = transformer.transform(lon, lat)

        # get trace as end coords in m relative to origin (WLG)
        print(f'trace coords: {q0.geometry[SECTION_IDX].coords.xy}')
        trace = transformer.transform(*q0.geometry[SECTION_IDX].coords.xy)
        print(f'trace offsets: {trace} (in metres relative to datum)')

        tile_dim = 30000
        vertical = int((q0.LowDepth[SECTION_IDX] - q0.UpDepth[SECTION_IDX]) * 1000)
        print(f"vertical offset: {vertical} metres")
        print(f"edge length:  {tile_dim} metres")

        lateral_x = int(math.sqrt(pow(tile_dim, 2) - pow(vertical, 2)))
        print(f"lateral x offset: {lateral_x} metres")

        xy = trace
        lon_diff = xy[0][0] - xy[0][1]
        lat_diff = xy[1][0] - xy[1][1]

        print(f'lon_diff: {lon_diff}, lat_diff: {lat_diff}')

        # lateral_y = int(math.sqrt(pow(lon_diff, 2) + pow(lat_diff, 2 )))
        print(f"lateral y offset: {lat_diff} metres")

        def plane_from_point_vector():
            p0 = g3d.Point(trace[0][0], trace[1][0], int(q0.UpDepth[SECTION_IDX] * 1000))
            v0 = g3d.Vector((lateral_x, lat_diff, vertical))

            # print(f"point p0 {p0}")
            # print(f"vector v0 {v0}")
            return g3d.Plane(p0, v0)

        def plane_from_3_points():
            p0 = g3d.Point(trace[0][0], trace[1][0], int(q0.UpDepth[SECTION_IDX] * 1000))  # 1st top-trace point
            p1 = g3d.Point(trace[0][1], trace[1][1], int(q0.UpDepth[SECTION_IDX] * 1000))  # 2nd top-trace point
            p2 = g3d.Point(  # point at new depth, and offs
                trace[0][0] - lateral_x, trace[1][0] - lat_diff, int(q0.LowDepth[SECTION_IDX] * 1000)
            )

            return g3d.Plane(p0, p1, p2)

        def pgram():
            p0 = g3d.Point(trace[0][0], trace[1][0], int(q0.UpDepth[SECTION_IDX] * 1000))
            v0 = g3d.Vector((lon_diff, lat_diff, 0))  #
            v1 = g3d.Vector((lateral_x, lat_diff, vertical))

            return g3d.Parallelogram(p0, v0, v1)

        p3p = plane_from_3_points()
        ppv = plane_from_point_vector()
        pg = pgram()
        print("3 plane_from_3_points", p3p)
        print()
        print("plane_from_point_vector", ppv)
        print()
        print('pg', pg)
        print('distance p3p: ', p3p.distance(datum))
        print('distance ppv: ', ppv.distance(g3d.origin()))

        print('distance pg: ', pg.distance(g3d.origin()))

        assert 0


def main():
    # This posp up a matplotlib window showing nothimg :(
    r = g3d.Renderer(backend='matplotlib')
    p0 = g3d.Point(0, 0, 0)
    p1 = g3d.Point(0, 1, 0)
    p2 = g3d.Point(0, 0, 1)
    p = g3d.Plane(p0, p1, p2)
    r.add((p, 'b', 1))

    b = g3d.Circle(g3d.origin(), g3d.y_unit_vector(), 10, 20)
    a = g3d.Circle(g3d.origin(), g3d.x_unit_vector(), 10, 20)
    c = g3d.Circle(g3d.origin(), g3d.z_unit_vector(), 10, 20)
    r.add((a, 'g', 3), 10)
    r.add((b, 'b', 3), 10)
    r.add((c, 'r', 3), 10)

    r.show()


if __name__ == '__main__':
    main()
