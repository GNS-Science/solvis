#! python test_geometry

import os
import pathlib
import unittest
from copy import deepcopy

from shapely.geometry import LineString, Point

import solvis
from solvis.geometry import bearing, dip_direction, refine_dip_direction

TEST_FOLDER = pathlib.PurePath(os.path.realpath(__file__)).parent.parent


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

    @unittest.skip('wait until rules figured out')
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

        # rdd = refine_dip_direction(point_a, point_b)
        # assert rdd == dd

    def test_dip_direction_crustal_refined_vs_original(self):
        def build_new_dip_dir_crustal(idx, section):
            points = section.geometry.coords.xy
            try:
                return refine_dip_direction(
                    Point(points[1][0], points[0][0]), Point(points[1][-1], points[0][-1]), section["DipDir"]
                )
            except (ValueError) as err:
                print(err)
                # raise

        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        original_solution = solvis.InversionSolution().from_archive(original_archive)

        fault_sections = deepcopy(original_solution.fault_sections)

        gt_n_degrees = 0
        for i, section in fault_sections.iterrows():
            dip_info = (
                i,
                section["DipDir"],
                build_new_dip_dir_crustal(i, section),
                fault_sections.FaultName[i],
                section.geometry,
            )
            diff = abs(dip_info[1] - dip_info[2])
            if diff > 10:
                print(f"diff: {diff}, info {dip_info}")
                gt_n_degrees += 1

        assert gt_n_degrees == 5


# def calc_orientation(idx, section):
#     assert type(section.geometry) == LineString
#     points = section.geometry.coords
#     point_a = tuple(reversed(points[0]))  # need lat/lon order
#     point_b = tuple(reversed(points[-1]))
#     return 'southing' if point_a[0] > point_b[0] else 'northing'


def calc_dip_dir(idx, section):
    assert type(section.geometry) == LineString
    points = section.geometry.coords
    point_a = tuple(reversed(points[0]))  # need lat/lon order
    point_b = tuple(reversed(points[-1]))

    if point_a[0] > point_b[0]:
        print('southing', point_a, point_b, section.FaultName)
        pass
    return refine_dip_direction(Point(*point_a), Point(*point_b), section.DipDir)


def calc_dip_error_margin(idx, section, dip, margin):
    diff = abs(section.DipDir - dip)
    if diff > margin:
        # print(section)
        print(
            f'idx: {idx}, abs({section.DipDir}-{dip}) = {diff}. '
            'Margin: {margin} DipDeg {section.DipDeg} DipDir: {section.DipDir}'
        )
        # raise AssertionError()
    return diff


class TestDipDirectionCrustal(unittest.TestCase):
    def setUp(self):
        original_archive = pathlib.PurePath(TEST_FOLDER, "fixtures/ModularAlpineVernonInversionSolution.zip")
        # original_archive = pathlib.PurePath(folder,
        #    "fixtures/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTQz.zip")
        original_solution = solvis.InversionSolution().from_archive(original_archive)
        self.fault_sections = deepcopy(original_solution.fault_sections)

    def test_fault_section_maxima(self):

        dip_dirs = [section.DipDir for idx, section in self.fault_sections.iterrows()]
        dip_degs = [section.DipDeg for idx, section in self.fault_sections.iterrows()]

        assert max(dip_dirs) < 360
        assert min(dip_dirs) > 0

        assert max(dip_degs) <= 90
        assert min(dip_degs) >= 0

    # @unittest.skip('wait until rules figured out')
    def test_fault_section_dip_direction_all_crustal(self):
        test = [
            calc_dip_error_margin(idx, section, calc_dip_dir(idx, section), 15)
            for idx, section in self.fault_sections.iterrows()
        ]
        assert max(test) < 30

    def test_fowlers_mean_dipdir(self):
        # Fowlers, Subsection 14"
        lines = [(i, section) for i, section in self.fault_sections.iterrows()]
        sectA = lines[47][1]
        sectB = lines[61][1]

        pointA = Point(*reversed(sectA.geometry.coords[0]))
        pointB = Point(*reversed(sectB.geometry.coords[1]))
        this_dd = refine_dip_direction(pointA, pointB, sectA.DipDir)

        self.assertAlmostEqual(this_dd, sectB.DipDir, -1)
        print(this_dd, sectB.DipDir)

    def test_fault_section_dip_direction_all_fowlers_sub_30(self):
        """
        fowlers is southing
        """

        """
        from CFM_1_0A_DOM_SANSTVZ
        <i123 sectionId="123" sectionName="Fowlers" aveLongTermSlipRate="0.50" slipRateStdDev="0.35"
            aveDip="90.0"
            aveRake="180.0" aveUpperDepth="0.0" aveLowerDepth="27.9" aseismicSlipFactor="0.0" couplingCoeff="1.0"
            dipDirection="163.0" parentSectionId="-1" connector="false" domainNo="14" domainName="Marlborough Fault System"> # noqa
          <FaultTrace name="Fowlers">
            <Location Latitude="-42.1869" Longitude="173.0723" Depth="0.0000"/>
            <Location Latitude="-42.2270" Longitude="173.0207" Depth="0.0000"/>
            <Location Latitude="-42.2747" Longitude="172.8393" Depth="0.0000"/>
            <Location Latitude="-42.3100" Longitude="172.7636" Depth="0.0000"/>
            <Location Latitude="-42.3166" Longitude="172.6605" Depth="0.0000"/>
            <Location Latitude="-42.3780" Longitude="172.3294" Depth="0.0000"/>
            <Location Latitude="-42.4048" Longitude="172.2430" Depth="0.0000"/>
            <Location Latitude="-42.4114" Longitude="172.1196" Depth="0.0000"/>
          </FaultTrace>
        </i123>

        """
        sections = list(self.fault_sections.iterrows())[47:][:14]
        test = [calc_dip_error_margin(idx, section, calc_dip_dir(idx, section), 15) for idx, section in sections]

        # orients = [calc_orientation(idx, section) for idx, section in sections]
        # print(orients)
        assert len(test) == 14
        assert max(test) < 30
        # assert 0

    def test_fault_section_dip_direction_all_barefell_sub_15(self):
        """
        barefell is 'northing' ...
        """

        """
        from CFM_1_0A_DOM_SANSTVZ
        <i35 sectionId="35" sectionName="Barefell" aveLongTermSlipRate="0.50" slipRateStdDev="0.38"
            aveDip="60.0"
            aveRake="160.0" aveUpperDepth="0.0" aveLowerDepth="28.9" aseismicSlipFactor="0.0" couplingCoeff="1.0"
            dipDirection="291.9" parentSectionId="-1" connector="false" domainNo="14" domainName="Marlborough Fault System"> # noqa
          <FaultTrace name="Barefell">
            <Location Latitude="-42.2460" Longitude="173.1168" Depth="0.0000"/>
            <Location Latitude="-42.1933" Longitude="173.1280" Depth="0.0000"/>
            <Location Latitude="-42.1150" Longitude="173.1780" Depth="0.0000"/>
            <Location Latitude="-42.0989" Longitude="173.1947" Depth="0.0000"/>
          </FaultTrace>
        </i35>
        """
        sections = list(self.fault_sections.iterrows())[62:][:3]
        test = [calc_dip_error_margin(idx, section, calc_dip_dir(idx, section), 0) for idx, section in sections]

        # orients = [calc_orientation(idx, section) for idx, section in sections]
        # print(orients)
        assert len(test) == 3
        assert max(test) < 15
        # assert 0

    def test_fault_section_dip_direction_all_alpine_j2k(self):
        """Alpine: Jacksons to Kaniere is northing"""

        """
        from CFM_1_0A_DOM_SANSTVZ

        <i13 sectionId="13" sectionName="Alpine: Jacksons to Kaniere" aveLongTermSlipRate="27.00" slipRateStdDev="5.00"
            aveDip="50.0"
            aveRake="160.0" aveUpperDepth="0.0" aveLowerDepth="22.3" aseismicSlipFactor="0.0" couplingCoeff="1.0"
            dipDirection="144.4" parentSectionId="-1" connector="false" domainNo="15" domainName="Alpine Fault">
          <FaultTrace name="Alpine: Jacksons to Kaniere">
            <Location Latitude="-44.0627" Longitude="168.7086" Depth="0.0000"/>
            <Location Latitude="-43.9019" Longitude="169.0844" Depth="0.0000"/>
            <Location Latitude="-43.7761" Longitude="169.3571" Depth="0.0000"/>
            <Location Latitude="-43.6370" Longitude="169.6656" Depth="0.0000"/>
            <Location Latitude="-43.4537" Longitude="170.0500" Depth="0.0000"/>
            <Location Latitude="-43.2257" Longitude="170.4862" Depth="0.0000"/>
            <Location Latitude="-43.0958" Longitude="170.7561" Depth="0.0000"/>
            <Location Latitude="-42.8914" Longitude="171.1464" Depth="0.0000"/>
          </FaultTrace>
        </i13>
        """

        sections = list(self.fault_sections.iterrows())[:30]
        test = [calc_dip_error_margin(idx, section, calc_dip_dir(idx, section), 0) for idx, section in sections]

        # orients = [calc_orientation(idx, section) for idx, section in sections]
        # print(orients)

        assert len(test) == 30
        assert max(test) < 30
        # assert 0
