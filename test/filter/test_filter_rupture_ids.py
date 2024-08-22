# from pytest import approx, raises
import importlib

import pytest
from nzshm_common.location.location import location_by_id

from solvis import circle_polygon


def test_top_level_import(fss):
    flt = importlib.import_module('solvis.filter')
    assert {0, 1, 2}.issubset(flt.FilterRuptureIds(fss).for_subsection_ids([1]))


def test_ruptures_for_subsections(filter_rupture_ids, filter_subsection_ids):
    ruptures = set([2, 3])
    assert filter_rupture_ids.for_subsection_ids(filter_subsection_ids.for_rupture_ids(ruptures)).issuperset(ruptures)


def test_ruptures_for_parent_fault_ids(filter_rupture_ids, filter_parent_fault_ids):
    fault_ids = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4'])
    rupt_ids_with_rate = filter_rupture_ids.for_parent_fault_ids(fault_ids)
    rupt_ids_all = filter_rupture_ids.for_parent_fault_ids(fault_ids, drop_zero_rates=False)

    assert rupt_ids_with_rate.issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )
    assert rupt_ids_all.issuperset(rupt_ids_with_rate)


def test_ruptures_for_parent_fault_names(filter_rupture_ids):
    assert filter_rupture_ids.for_parent_fault_names(['Vernon 4']).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )


def test_ruptures_for_polygon_intersecting(fss, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    print(rupture_ids)

    # check vs the legacy solvis function
    assert rupture_ids == set(fss.get_rupture_ids_intersecting(polygon))

    # check vs known fixture values
    assert set(
        [68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 2988, 2989, 3001, 3002, 3004, 3018, 3031, 3042, 3043, 3054]
    ).issubset(rupture_ids)


def test_ruptures_for_polygon_intersecting_with_drop_zero(fss, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    all_rupture_ids = filter_rupture_ids.for_polygon(polygon, drop_zero_rates=False)
    assert all_rupture_ids.issuperset(rupture_ids)
    assert len(all_rupture_ids) > len(rupture_ids)


@pytest.mark.skip('WIP')
def test_ruptures_for_polygon_intersecting_with_contained(fss, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon, contained=True)  # noqa

    # all_rupture_ids = filter_rupture_ids.for_polygon(polygon, drop_zero_rates=False)
    # assert all_rupture_ids.issuperset(rupture_ids)
    # assert len(all_rupture_ids) > len(rupture_ids)


@pytest.mark.parametrize("drop_zero_input", [True, False])
def test_ruptures_for_min_mag(filter_rupture_ids, drop_zero_input):
    m6plus = filter_rupture_ids.for_magnitude(min_mag=6.0, drop_zero_rates=drop_zero_input)
    m7plus = filter_rupture_ids.for_magnitude(min_mag=7.0, drop_zero_rates=drop_zero_input)

    assert len(m6plus)
    assert len(m7plus)
    assert m6plus.issuperset(m7plus)
    assert m6plus.difference(m7plus) == filter_rupture_ids.for_magnitude(
        min_mag=6.0, max_mag=7.0, drop_zero_rates=drop_zero_input
    )


@pytest.mark.parametrize("drop_zero_input", [True, False])
def test_ruptures_for_max_mag(filter_rupture_ids, drop_zero_input):
    m8less = filter_rupture_ids.for_magnitude(max_mag=8.0, drop_zero_rates=drop_zero_input)
    m7less = filter_rupture_ids.for_magnitude(max_mag=7.5, drop_zero_rates=drop_zero_input)

    assert len(m8less)
    assert len(m7less)
    assert m7less.issubset(m8less)
    assert m8less.difference(m7less) == filter_rupture_ids.for_magnitude(
        min_mag=7.5, max_mag=8.0, drop_zero_rates=drop_zero_input
    )


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_rate(filter_rupture_ids, drop_zero_rates):
    r6less = filter_rupture_ids.for_rupture_rate(min_rate=1e-6, drop_zero_rates=drop_zero_rates)
    r7less = filter_rupture_ids.for_rupture_rate(min_rate=1e-7, drop_zero_rates=drop_zero_rates)

    assert len(r6less)
    assert len(r7less)
    assert r6less.issubset(r7less)
    assert r7less.difference(r6less) == filter_rupture_ids.for_rupture_rate(
        min_rate=1e-7, max_rate=1e-6, drop_zero_rates=drop_zero_rates
    )
    # if not drop_zero_rates:
    #     print(list(r7less.difference(r6less))[:10])
    #     assert 0
