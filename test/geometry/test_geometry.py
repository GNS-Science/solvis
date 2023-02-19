#! python test_geometry

import unittest

import numpy as np
from shapely.geometry import LineString, Point

from solvis.geometry import bearing, circle_polygon, strike


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


class TestBearing(unittest.TestCase):
    def test_simple_45(self):
        point_a = Point(0, 0)
        point_b = Point(1, 1)
        self.assertAlmostEqual(bearing(point_a, point_b), 45.0, 2)

    def test_simple_90(self):
        point_a = Point(0, 0)
        point_b = Point(0, 1)
        assert bearing(point_a, point_b) == 90.0

    def test_simple_135(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 1)
        self.assertAlmostEqual(bearing(point_a, point_b), 135.0, 2)

    def test_simple_180(self):
        point_a = Point(0, 0)
        point_b = Point(-1, 0)
        assert bearing(point_a, point_b) == 180.0

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

    def test_bearing_simple_usa(self):
        """ "
        example from https://www.igismap.com/formula-to-find-bearing-or-heading-angle-between-two-points-latitude-longitude/  # noqa
        """
        point_a = Point(39.099912, -94.581213)  # Kansas City
        point_b = Point(38.627089, -90.200203)  # St Louis
        self.assertAlmostEqual(bearing(point_a, point_b), 96.51, 2)
