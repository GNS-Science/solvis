# from pytest import approx, raises
import importlib

import pytest
from nzshm_common.location.location import location_by_id

from solvis import circle_polygon
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.solution.typing import SetOperationEnum

# TODO: these tests should also cover InversionSolution, not just FSS


def test_top_level_import(crustal_solution_fixture):
    flt = importlib.import_module('solvis.filter')
    assert {0, 1, 2}.issubset(flt.FilterRuptureIds(crustal_solution_fixture).for_subsection_ids([1]))


def test_filter_inversion_solution_or_model(crustal_solution_fixture):
    rupts_a = FilterRuptureIds(crustal_solution_fixture).all()
    rupts_b = FilterRuptureIds(crustal_solution_fixture.model).all()
    assert rupts_a == rupts_b


def test_filter_fault_system_solution_or_model(crustal_small_fss_fixture):
    rupts_a = FilterRuptureIds(crustal_small_fss_fixture).all()
    rupts_b = FilterRuptureIds(crustal_small_fss_fixture.model).all()
    assert rupts_a == rupts_b


def test_ruptures_all(filter_rupture_ids, crustal_solution_fixture):
    all_ruptures = filter_rupture_ids.all()
    print(list(all_ruptures))
    assert len(all_ruptures) == crustal_solution_fixture.solution_file.ruptures.shape[0]


def test_ruptures_for_subsections(filter_rupture_ids, filter_subsection_ids):
    ruptures = set([2, 3])
    all_rupts = filter_rupture_ids.for_subsection_ids(filter_subsection_ids.for_rupture_ids(ruptures))

    print(all_rupts, ruptures)
    assert all_rupts.issuperset(ruptures)


def test_ruptures_for_parent_fault_ids(filter_rupture_ids, filter_parent_fault_ids, crustal_solution_fixture):
    fault_ids = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4'])
    rupt_ids_with_rate = filter_rupture_ids.for_parent_fault_ids(fault_ids)
    rupt_ids_all = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_parent_fault_ids(fault_ids)

    assert rupt_ids_with_rate.issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )
    assert rupt_ids_all.issuperset(rupt_ids_with_rate)


def test_ruptures_for_parent_fault_names(filter_rupture_ids):
    assert filter_rupture_ids.for_parent_fault_names(['Vernon 4']).issuperset(
        set([2090, 2618, 1595, 76, 77, 594, 595, 2134, 1126, 1127, 1648, 1649, 2177, 664, 665, 154, 2723])
    )


def test_ruptures_for_polygon_intersecting(crustal_solution_fixture, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    # check vs the legacy solvis function - now Deprecated
    # assert rupture_ids == set(crustal_solution_fixture.get_rupture_ids_intersecting(polygon))

    # check vs known fixture values
    assert set(
        [68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 2988, 2989, 3001, 3002, 3004, 3018, 3031, 3042, 3043, 3054]
    ).issubset(rupture_ids)


def test_ruptures_for_polygons_join_iterable(crustal_solution_fixture, filter_rupture_ids):
    WLG = location_by_id('WLG')
    MRO = location_by_id('MRO')
    polyA = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    polyB = circle_polygon(1.5e5, MRO['latitude'], MRO['longitude'])  # 150km circle around MRO

    ridsA = filter_rupture_ids.for_polygons([polyA])
    ridsB = filter_rupture_ids.for_polygons([polyB])

    print(set(ridsA))
    print(set(ridsB))

    # default == union
    assert filter_rupture_ids.for_polygons([polyA, polyB]) == ridsA.union(ridsB)

    # intersection
    assert filter_rupture_ids.for_polygons(
        [polyA, polyB], join_polygons=SetOperationEnum.INTERSECTION
    ) == ridsA.intersection(ridsB)

    # union
    assert filter_rupture_ids.for_polygons([polyA, polyB], join_polygons=SetOperationEnum.UNION) == ridsA.union(ridsB)

    # difference
    assert filter_rupture_ids.for_polygons(
        [polyA, polyB], join_polygons='difference'  # SetOperationEnum.DIFFERENCE'
    ) == ridsA.difference(ridsB)


@pytest.mark.skip("investigate!")
def test_ruptures_for_polygon_intersecting_with_drop_zero(crustal_solution_fixture, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    all_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_polygon(polygon)
    assert all_rupture_ids.issuperset(rupture_ids)
    assert len(all_rupture_ids) > len(rupture_ids)


@pytest.mark.skip("investigate!")
def test_ruptures_for_polygon_intersecting_with_drop_zero_fss(fss_crustal, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    all_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=False).for_polygon(polygon)
    assert all_rupture_ids.issuperset(rupture_ids)
    assert len(all_rupture_ids) > len(rupture_ids)


@pytest.mark.skip('IS & FSS differ - INVESTIGATE')
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_mag(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    m6plus = filter_rupture_ids.for_magnitude(min_mag=6.0)
    m7plus = filter_rupture_ids.for_magnitude(min_mag=7.0)

    assert len(m6plus)
    assert len(m7plus)
    assert m6plus.issuperset(m7plus)
    assert m6plus.difference(m7plus) == filter_rupture_ids.for_magnitude(min_mag=6.0, max_mag=7.0)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_mag_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    m6plus = filter_rupture_ids.for_magnitude(min_mag=6.0)
    m7plus = filter_rupture_ids.for_magnitude(min_mag=7.0)

    assert len(m6plus)
    assert len(m7plus)
    assert m6plus.issuperset(m7plus)
    assert m6plus.difference(m7plus) == filter_rupture_ids.for_magnitude(min_mag=6.0, max_mag=7.0)


@pytest.mark.skip('IS & FSS differ - INVESTIGATE')
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_max_mag(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    m8less = filter_rupture_ids.for_magnitude(max_mag=8.0)
    m7less = filter_rupture_ids.for_magnitude(max_mag=7.5)

    assert len(m8less)
    assert len(m7less)
    assert m7less.issubset(m8less)
    assert m8less.difference(m7less) == filter_rupture_ids.for_magnitude(min_mag=7.5, max_mag=8.0)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_max_mag_FSS(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    m8less = filter_rupture_ids.for_magnitude(max_mag=8.0)
    m7less = filter_rupture_ids.for_magnitude(max_mag=7.5)

    assert len(m8less)
    assert len(m7less)
    assert m7less.issubset(m8less)
    assert m8less.difference(m7less) == filter_rupture_ids.for_magnitude(min_mag=7.5, max_mag=8.0)


@pytest.mark.skip('IS & FSS differ - INVESTIGATE')
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_rate(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    r6less = filter_rupture_ids.for_rupture_rate(min_rate=1e-6)
    r7less = filter_rupture_ids.for_rupture_rate(min_rate=1e-7)

    assert len(r6less)
    assert len(r7less)
    assert r6less.issubset(r7less)
    assert r7less.difference(r6less) == filter_rupture_ids.for_rupture_rate(min_rate=1e-7, max_rate=1e-6)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_rate_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    r6less = filter_rupture_ids.for_rupture_rate(min_rate=1e-6)
    r7less = filter_rupture_ids.for_rupture_rate(min_rate=1e-7)

    assert len(r6less)
    assert len(r7less)
    assert r6less.issubset(r7less)
    assert r7less.difference(r6less) == filter_rupture_ids.for_rupture_rate(min_rate=1e-7, max_rate=1e-6)


@pytest.mark.skip('IS & FSS differ - INVESTIGATE')
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_filter_chaining_rates(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    r6less = filter_rupture_ids.for_rupture_rate(min_rate=1e-6)
    r7less = filter_rupture_ids.for_rupture_rate(min_rate=1e-7)

    chained = filter_rupture_ids.for_rupture_rate(min_rate=1e-7).for_rupture_rate(max_rate=1e-6)

    assert r7less.difference(r6less) == chained


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_filter_chaining_rates_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    r6less = filter_rupture_ids.for_rupture_rate(min_rate=1e-6)
    r7less = filter_rupture_ids.for_rupture_rate(min_rate=1e-7)

    chained = filter_rupture_ids.for_rupture_rate(min_rate=1e-7).for_rupture_rate(max_rate=1e-6)

    assert r7less.difference(r6less) == chained


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_filter_chaining_join_chain(crustal_solution_fixture, drop_zero_rates):
    frids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    n0 = frids.for_parent_fault_names(['Vernon 4'])
    n1 = frids.for_parent_fault_names(['Alpine Jacksons to Kaniere'])
    chained_default = frids.for_parent_fault_names(['Vernon 4']).for_parent_fault_names(['Alpine Jacksons to Kaniere'])
    assert n1.intersection(n0) == chained_default

    chained_intersect = frids.for_parent_fault_names(['Vernon 4']).for_parent_fault_names(
        ['Alpine Jacksons to Kaniere'], join_prior=SetOperationEnum.INTERSECTION
    )
    assert n1.intersection(n0) == chained_intersect

    chained_union = frids.for_parent_fault_names(['Vernon 4']).for_parent_fault_names(
        ['Alpine Jacksons to Kaniere'], join_prior='union'  # SetOperationEnum.UNION
    )
    assert n1.union(n0) == chained_union

    chained_diff = frids.for_parent_fault_names(['Vernon 4']).for_parent_fault_names(
        ['Alpine Jacksons to Kaniere'], join_prior='difference'  # SetOperationEnum.DIFFERENCE
    )
    assert n1.difference(n0) == chained_diff


def test_filter_invalid_polygon_join_raises(filter_rupture_ids):
    WLG = location_by_id('WLG')
    polyA = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG

    with pytest.raises(ValueError) as exc:
        filter_rupture_ids.for_polygons([polyA], join_polygons='bad')

    assert "Unsupported set operation `bad` for `join_polygons` argument" in str(exc)
