#! python test_circle_polygon.py

import unittest

import numpy as np
from shapely.geometry import LineString

from solvis import circle_polygon


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
