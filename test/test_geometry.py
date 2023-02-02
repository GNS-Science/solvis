#! python test_geometry

import os
import pathlib
import unittest
from copy import deepcopy

import numpy as np
from shapely.geometry import LineString, Point

import solvis
from solvis.geometry import bearing, circle_polygon, create_surface, dip_direction, strike


class TestCirclePoly(unittest.TestCase):
    def test_no_negative_lats_in_circle_polygon(self):

        # using Gisborne 200km example
        polygon = circle_polygon(2e5, -38.662334, 178.017654)

        lat, lon = np.hsplit(np.asarray(polygon.exterior.coords), 2)
        assert min(lat) >= 0


class TestCirclePolyIntersections(unittest.TestCase):
    def test_enclosed_line_is_intersecting_line(self):

        polygon = circle_polygon(2e5, -38.662334, 178.017654)
        line = LineString([[178.017654, -38.662334], [178.017654, -38.762334]])

        self.assertTrue(line.intersects(polygon))
        self.assertTrue(line.within(polygon))
        self.assertTrue(polygon.contains(line))

    def test_crossing_line_is_intersecting_line(self):

        polygon = circle_polygon(2e5, -38.662334, 178.017654)
        line = LineString([[178.017654, -38.662334], [170.017654, -38.662334]])

        self.assertTrue(line.intersects(polygon))
        self.assertTrue(line.crosses(polygon))
        self.assertFalse(polygon.contains(line))

    def test_external_line_is_not_intersecting_line(self):

        polygon = circle_polygon(2e5, -38.662334, 178.017654)
        line = LineString([[171.017654, -38.662334], [170.017654, -38.662334]])

        self.assertFalse(line.intersects(polygon))
        self.assertFalse(line.within(polygon))
        self.assertFalse(polygon.contains(line))


class TestBearing_aka_Strike(unittest.TestCase):
    def test_simple_45(self):
        point_a = Point(0, 0)
        point_b = Point(1, 1)
        self.assertAlmostEqual(bearing(point_a, point_b), 45.0, 2)

    def test_simple_90(self):
        point_a = Point(0, 0)
        point_b = Point(0, 1)
        assert bearing(point_a, point_b) == 90.0

    def test_simple_180(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 0)
        assert bearing(point_a, point_b) == 180.0

    def test_simple_135(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 1)
        self.assertAlmostEqual(bearing(point_a, point_b), 135.0, 2)

    def test_identical_points_raise_value_error(self):
        point_a = Point(0, 0)
        point_b = Point(0, 0)
        with self.assertRaises(ValueError):
            bearing(point_a, point_b)

    def test_strike_alias_for_bearing_45(self):
        point_a = Point(0, 0)
        point_b = Point(1, 1)
        self.assertAlmostEqual(strike(point_a, point_b), 45.0, 2)

    def test_bearing_alpine_0(self):
        point_a = Point(-44.0627, 168.7086)  # lat, lon
        assert point_a.x == -44.0627
        assert point_a.y == 168.7086

        point_b = Point(-44.02781681586314, 168.7905428698305)
        assert point_b.x == -44.02781681586314
        assert point_b.y == 168.7905428698305
        self.assertAlmostEqual(bearing(point_a, point_b), 59.39, 2)

    # def test_bearing_simple_usa(self):
    #     # Kansas City: 39.099912, -94.581213
    #     # St Louis: 38.627089, -90.200203
    #     point_a = Point(39.099912, -94.581213) # lat, lon
    #     point_b = Point(38.627089, -90.200203)
    #     self.assertAlmostEqual(bearing(point_a, point_b), 96.51, 2)
    #     self.assertAlmostEqual(bearing_simple(point_a.x, point_a.y, point_b.x, point_b.y), 96.51, 2)

    # def test_bearing_simple(self):
    #     point_a = Point(-44.0627, 168.7086) # lat, lon
    #     assert point_a.x == -44.0627
    #     assert point_a.y == 168.7086

    #     point_b = Point(-44.02781681586314, 168.7905428698305)
    #     assert point_b.x == -44.02781681586314
    #     assert point_b.y == 168.7905428698305
    #     self.assertAlmostEqual(bearing_simple(point_a.x, point_a.y, point_b.x, point_b.y), 59.39, 2)


def build_new_dip_dir(idx, section):
    # points can be any array, depending on section complexity, but why sometimes last point is duplicated ??
    print('idx', idx, 'geometry', section["geometry"])
    # points = section["geometry"].exterior.coords[:-1]
    # print(len(points))

    # print(type(section.geometry.exterior.coords.xy))
    coords = section.geometry.exterior.coords.xy
    # if len(coords[0])/2 >= int(len(coords[0])/2):
    #     print(f'trace coords: {coords[0]}, {coords[1]}')
    #     print('original_solution.fault_sections', original_solution.fault_sections.geometry[idx])
    #     return 0
    #     raise ValueError()

    btm_idx = int((len(coords[0]) - 1) / 2)
    points = coords  # transformer.transform(coords[0], coords[1])

    print(f'trace coords: {coords[0]}, {coords[1]}')
    print('btm_idx ', btm_idx)
    print('points', points)

    # if len(coords[0]) == 5:
    #     points = transformer.transform(coords[0][:-1], coords[1][:-1])
    #     print(f'trace coords: {coords[0][:-1]}, {coords[1][:-1]}')
    # elif len(coords[0]) == 4:
    #     points = transformer.transform(coords[0], coords[1])
    #     print(f'trace coords: {coords[0]}, {coords[1]}')
    # else:
    #     print(f'trace coords: {coords[0]}, {coords[1]}')
    #     print('original_solution.fault_sections', original_solution.fault_sections.geometry[idx])
    #     assert 0

    # print(len(points[0]), points)
    # assert len(points[0]) == 4

    # bottom_idx = int(len(points)/2)
    # print(bottom_idx)
    # surface = pv.PolyData(
    #     [
    #         [points[0][0], points[0][1], int(section['UpDepth'] * 1000)],
    #         [points[bottom_idx-1][0], points[bottom_idx-1][1], int(section['UpDepth'] * 1000)],
    #         [points[bottom_idx][0], points[bottom_idx][1], int(section['LowDepth'] * 1000)],
    #         [points[-1][0], points[-1][1], int(section['LowDepth'] * 1000)],
    #     ]
    # )

    try:
        return dip_direction(Point(points[0][0], points[1][0]), Point(points[0][btm_idx - 1], points[1][btm_idx - 1]))
    except (ValueError) as err:
        print(err)


class TestDipDirection(unittest.TestCase):
    def test_simple_45(self):
        point_a = Point(0, 0)
        point_b = Point(1, 1)
        self.assertAlmostEqual(dip_direction(point_a, point_b), 45.0 + 90, 2)

    def test_simple_90(self):
        point_a = Point(0, 0)
        point_b = Point(0, 1)
        assert dip_direction(point_a, point_b) == 90.0 + 90

    def test_simple_180(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 0)
        assert dip_direction(point_a, point_b) == 180.0 + 90

    def test_simple_135(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 1)
        self.assertAlmostEqual(dip_direction(point_a, point_b), 135.0 + 90, 2)

    def test_identical_points_raise_value_error(self):
        point_a = Point(0, 0)
        point_b = Point(0, 0)
        with self.assertRaises(ValueError) as err:
            dip_direction(point_a, point_b)
            print(err)

    def test_fault_section_dip_direction_0(self):
        # LINESTRING (168.7086 -44.0627, 168.7905428698305 -44.02781681586314)
        # geometry = 'POLYGON ((168.7086 -44.0627, 168.7905428698305 -44.02781681586314, 168.8639492164901
        # -44.10142314655593, 168.7820496972809 -44.13630630204676, 168.7086 -44.0627))'
        coords = [
            [168.7086, 168.7905428698305, 168.8639492164901, 168.7820496972809, 168.7086],
            [-44.0627, -44.02781681586314, -44.10142314655593, -44.13630630204676, -44.0627],
        ]
        btm_idx = int((len(coords[0]) - 1) / 2)
        points = coords  # transformer.transform(coords[0], coords[1])

        print(points)
        point_a = Point(points[1][0], points[0][0])
        point_b = Point(points[1][btm_idx - 1], points[0][btm_idx - 1])

        print(point_a, point_b)

        assert point_a.x == -44.0627
        assert point_a.y == 168.7086

        assert point_b.x == -44.02781681586314
        assert point_b.y == 168.7905428698305

        bb = bearing(point_a, point_b)
        self.assertAlmostEqual(bb, 59.39, 2)
        dd = dip_direction(point_a, point_b)
        print(dd)
        # assert dd == 144.0 # desired value from section
        self.assertAlmostEqual(dd, 59.39 + 90, 2)

    # def NOtest_fault_section_dip_direction_1(self):
    #     # LINESTRING (168.7086 -44.0627, 168.7905428698305 -44.02781681586314)
    #     # geometry = 'POLYGON ((168.7086 -44.0627, 168.7905428698305 -44.02781681586314, 168.8639492164901
    #     #  -44.10142314655593, 168.7820496972809 -44.13630630204676, 168.7086 -44.0627))'
    #     coords = [
    #         [168.7086, 168.7905428698305, 168.8639492164901, 168.7820496972809, 168.7086],
    #         [-44.0627, -44.02781681586314, -44.10142314655593, -44.13630630204676, -44.0627]
    #     ]
    #     btm_idx = int((len(coords[0])-1)/2)

    #     from pyproj import Transformer

    #     wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
    #     local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(-44.0627, 168.7086)
    #     transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
    #     # datum = transformer.transform(lon, lat)

    #     points = coords # transformer.transform(coords[0], coords[1])
    #     points = transformer.transform(coords[0], coords[1])

    #     print(points)
    #     point_a  = Point(points[1][0], points[0][0])
    #     point_b =  Point(points[1][btm_idx-1], points[0][btm_idx-1])

    #     print(point_a, point_b)

    #     # assert point_a.x == -44.0627
    #     # assert point_a.y == 168.7086

    #     # assert point_b.x == -44.02781681586314
    #     # assert point_b.y == 168.7905428698305

    #     bb = bearing(point_a, point_b)
    #     assert bb == 60
    #     dd = dip_direction(point_a, point_b)
    #     print(dd)
    #     assert dd == 144.0

    @unittest.skip('wip')
    def test_fault_section_dip_direction(self):

        folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        original_archive = pathlib.PurePath(folder, "fixtures/ModularAlpineVernonInversionSolution.zip")
        original_solution = solvis.InversionSolution().from_archive(original_archive)

        fault_sections = deepcopy(original_solution.fault_sections)

        print(fault_sections[["FaultID", "DipDeg", "DipDir", "geometry"]])

        print(fault_sections.geometry[0], fault_sections.DipDir[0])

        def create_section_surface(section):
            return create_surface(
                section["geometry"], section["DipDir"], section["DipDeg"], section["UpDepth"], section["LowDepth"]
            )

        polys = [create_section_surface(section) for i, section in fault_sections.iterrows()]
        # print(polys[0])
        fault_sections = fault_sections.set_geometry(polys)

        # print("After set", fault_sections["geometry"][0])

        # TODO calculate lower trace lat & lon based on dip_direction
        # new_polys = [create_section_surface(section) for i, section in self.fault_sections.iterrows()]

        # WLG = location_by_id('WLG')
        # lon, lat = WLG['longitude'], WLG['latitude']
        # print(f'datum: {WLG}')

        # wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        # local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        # transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
        # datum = transformer.transform(lon, lat)

        dip_dir = [build_new_dip_dir(i, section) for i, section in fault_sections.iterrows()]
        print(dip_dir)

        print([section.DipDir for i, section in fault_sections.iterrows()])

        # assert 0
