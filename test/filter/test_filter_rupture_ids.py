# from pytest import approx, raises
from nzshm_common.location.location import location_by_id

from solvis import circle_polygon


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
    assert rupture_ids == set(fss.get_rupture_ids_intersecting(polygon))  # check vs the legacy solvis function
    assert set(
        [68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 2988, 2989, 3001, 3002, 3004, 3018, 3031, 3042, 3043, 3054]
    ).issubset(rupture_ids)
