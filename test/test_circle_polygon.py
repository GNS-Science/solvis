#! python test_circle_polygon.py

import unittest
from solvis import circle_polygon
import numpy as np

class TestCirclePoly(unittest.TestCase):

    def test_no_negative_lats_in_circle_polygon(self):

        #using Gisborne 200km example
        polygon = circle_polygon(2e5, -38.662334, 178.017654)

        lat, lon = np.hsplit(np.asarray(polygon.exterior.coords),2)
        assert min(lat) >= 0

