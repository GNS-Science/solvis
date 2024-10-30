import os
import pathlib
import timeit
import unittest

import geopandas as gpd
import pytest
from nzshm_common.location.location import location_by_id
from pyproj import Transformer

from solvis import InversionSolution, geometry

TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent


class TestDipDirectionCrustal(unittest.TestCase):
    @pytest.mark.performance
    def test_calc_performance_to_a_crustal_fault_section(self):

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        sol = InversionSolution().from_archive(original_archive)

        # pick a rupture section
        gdf = gpd.GeoDataFrame(sol.fault_surfaces())

        # # set up WLG as our datum
        WLG = location_by_id('WLG')
        lon, lat = WLG['longitude'], WLG['latitude']

        wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"
        local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
        transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)

        # time it takes to execute the main statement a number of times, measured in seconds as a float.
        count = 10
        elapsed = (
            timeit.timeit(
                lambda: gdf.apply(
                    lambda section: geometry.section_distance(
                        transformer, section.geometry, section.UpDepth, section.LowDepth
                    ),
                    axis=1,
                ),
                number=count,
            )
            / 10
        )
        assert elapsed < 0.1  # 100msec

    @pytest.mark.performance
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

        count = 10
        elapsed = (
            timeit.timeit(
                lambda: gdf.apply(
                    lambda section: geometry.section_distance(
                        transformer, section.geometry, section.UpDepth, section.LowDepth
                    ),
                    axis=1,
                ),
                number=count,
            )
            / 10
        )
        assert elapsed < 0.5  # 500msec
