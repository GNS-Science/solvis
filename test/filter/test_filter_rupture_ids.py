# from pytest import approx, raises
import importlib

import pytest
from nzshm_common.location.location import location_by_id

from solvis.filter.rupture_id_filter import FilterRuptureIds, FilterSubsectionIds
from solvis.geometry import circle_polygon
from solvis.solution.typing import SetOperationEnum

# TODO: these tests should also cover InversionSolution, not just FSS


def test_top_level_import(crustal_solution_fixture):
    flt = importlib.import_module('solvis.filter')
    assert {0, 1, 2}.issubset(
        flt.FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_subsection_ids([1])
    )


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


def test_ruptures_for_subsections(crustal_solution_fixture, filter_subsection_ids):
    ruptures = set([2, 3])
    all_rupts = FilterRuptureIds(crustal_solution_fixture, False).for_subsection_ids(
        filter_subsection_ids.for_rupture_ids(ruptures)
    )

    print(all_rupts, ruptures)
    assert all_rupts.issuperset(ruptures)


@pytest.mark.parametrize("drop_zero_rates, len_sects, len_rupts", [(True, 5, 126), (False, 5, 380)])
def test_ruptures_for_subsections_with_drop_zero_rates(
    crustal_solution_fixture, filter_subsection_ids, drop_zero_rates, len_sects, len_rupts
):
    ruptures = set([2, 3])
    ssids = list(filter_subsection_ids.for_rupture_ids(ruptures))
    rupt_ids = list(
        FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates).for_subsection_ids(ssids)
    )
    assert len(ssids) == len_sects
    assert len(rupt_ids) == len_rupts


def test_ruptures_for_parent_fault_ids(filter_rupture_ids, filter_parent_fault_ids, crustal_solution_fixture):
    fault_ids = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4', 'Alpine Jacksons to Kaniere']).tolist()

    rupt_ids_with_rate = filter_rupture_ids.for_parent_fault_ids(fault_ids)
    rupt_ids_all = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_parent_fault_ids(fault_ids)

    print(fault_ids)

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


def test_ruptures_for_polygon_type(crustal_solution_fixture, filter_rupture_ids):
    MRO = location_by_id('MRO')
    poly = circle_polygon(1.5e5, MRO['latitude'], MRO['longitude'])  # 150km circle around MRO
    rids = filter_rupture_ids.for_polygon(poly)
    assert isinstance(list(rids)[0], int)


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
        [polyA, polyB], join_type=SetOperationEnum.INTERSECTION
    ) == ridsA.intersection(ridsB)

    # union
    assert filter_rupture_ids.for_polygons([polyA, polyB], join_type=SetOperationEnum.UNION) == ridsA.union(ridsB)

    # difference
    assert filter_rupture_ids.for_polygons(
        [polyA, polyB], join_type='difference'  # SetOperationEnum.DIFFERENCE'
    ) == ridsA.difference(ridsB)


# @pytest.mark.skip("investigate!")
def test_ruptures_for_polygon_intersecting_with_drop_zero(crustal_solution_fixture, filter_rupture_ids):
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    all_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_polygon(polygon)
    assert all_rupture_ids.issuperset(rupture_ids)
    assert len(all_rupture_ids) >= len(rupture_ids)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_polygon_intersecting_with_drop_zero_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)
    WLG = location_by_id('WLG')
    polygon = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG
    rupture_ids = filter_rupture_ids.for_polygon(polygon)

    all_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=False).for_polygon(polygon)
    assert all_rupture_ids.issuperset(rupture_ids)
    assert len(all_rupture_ids) >= len(rupture_ids)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_mag_with_drop_zero(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)
    m6plus = filter_rupture_ids.for_magnitude(min_mag=6.0)
    m7plus = filter_rupture_ids.for_magnitude(min_mag=7.0)

    assert len(m6plus)
    assert len(m7plus)
    assert m6plus.issuperset(m7plus)
    assert m6plus.difference(m7plus) == filter_rupture_ids.for_magnitude(min_mag=6.0, max_mag=7.0)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_min_mag_with_drop_zero_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    m6plus = filter_rupture_ids.for_magnitude(min_mag=6.0)
    m7plus = filter_rupture_ids.for_magnitude(min_mag=7.0)

    assert len(m6plus)
    assert len(m7plus)
    assert m6plus.issuperset(m7plus)
    assert m6plus.difference(m7plus) == filter_rupture_ids.for_magnitude(min_mag=6.0, max_mag=7.0)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_max_mag_with_drop_zero(crustal_solution_fixture, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    m8less = filter_rupture_ids.for_magnitude(max_mag=8.0)
    m7less = filter_rupture_ids.for_magnitude(max_mag=7.5)

    assert len(m8less)
    assert len(m7less)
    assert m7less.issubset(m8less)
    assert m8less.difference(m7less) == filter_rupture_ids.for_magnitude(min_mag=7.5, max_mag=8.0)


@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_max_mag_with_drop_zero_fss(fss_crustal, drop_zero_rates):
    filter_rupture_ids = FilterRuptureIds(fss_crustal, drop_zero_rates=drop_zero_rates)

    m8less = filter_rupture_ids.for_magnitude(max_mag=8.0)
    m7less = filter_rupture_ids.for_magnitude(max_mag=7.5)

    assert len(m8less)
    assert len(m7less)
    assert m7less.issubset(m8less)
    assert m8less.difference(m7less) == filter_rupture_ids.for_magnitude(min_mag=7.5, max_mag=8.0)


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


# @pytest.mark.skip('IS & FSS differ - INVESTIGATE')
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

    FAULT0 = 'Vernon 4'
    FAULT1 = 'Alpine Jacksons to Kaniere'

    n0 = set(frids.for_parent_fault_names([FAULT0]))
    n1 = set(frids.for_parent_fault_names([FAULT1]))

    chained_default = frids.for_parent_fault_names([FAULT0]).for_parent_fault_names([FAULT1])
    assert n1.intersection(n0) == chained_default

    chained_intersect = frids.for_parent_fault_names([FAULT0]).for_parent_fault_names(
        [FAULT1], join_prior=SetOperationEnum.INTERSECTION
    )

    print(chained_intersect.tolist())
    assert n1.intersection(n0) == chained_intersect

    chained_union = frids.for_parent_fault_names([FAULT0]).for_parent_fault_names(
        [FAULT1], join_prior='union'  # , SetOperationEnum.UNION
    )

    print("len(n0)", len(n0))
    print("len(n1)", len(n1))
    print("len(n1.intersection(n0))", len(n1.intersection(n0)))
    print("list(n1.intersection(n0))", list(n1.intersection(n0)))
    print()
    print("len(n1.union(n0))", len(n1.union(n0)))
    print("len(chained_union.tolist())", len(chained_union.tolist()))

    assert chained_union.issuperset(n0)
    assert chained_union.issuperset(n1)

    print(n1.union(n0).difference(chained_union))
    assert n1.union(n0) == set(chained_union)

    chained_diff = frids.for_parent_fault_names([FAULT0]).for_parent_fault_names(
        [FAULT1], join_prior='difference'  # SetOperationEnum.DIFFERENCE
    )
    assert n1.difference(n0) == chained_diff


def test_filter_invalid_polygon_join_raises(filter_rupture_ids):
    WLG = location_by_id('WLG')
    polyA = circle_polygon(1e5, WLG['latitude'], WLG['longitude'])  # 100km circle around WLG

    with pytest.raises(ValueError) as exc:
        filter_rupture_ids.for_polygons([polyA], join_type='bad')

    assert "Unsupported set operation `bad` for `join_type` argument" in str(exc)


def test_ruptures_filtered_with_vs_without_drop_zero(crustal_solution_fixture):
    M = 5.7
    rupture_ids_0 = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_magnitude(min_mag=M)
    rupture_ids_1 = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=True).for_magnitude(min_mag=M)

    assert (len(list(rupture_ids_0.symmetric_difference(rupture_ids_1)))) > 0


@pytest.mark.parametrize("intersection_join", ['intersection', SetOperationEnum.INTERSECTION])
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_parent_fault_ids_set_operations(
    filter_parent_fault_ids, crustal_solution_fixture, drop_zero_rates, intersection_join
):

    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    fault_ids = filter_parent_fault_ids.for_parent_fault_names(['Vernon 4', 'Alpine Jacksons to Kaniere']).tolist()

    rupt_ids_union = filter_rupture_ids.for_parent_fault_ids(fault_ids, join_type='union')
    rupt_ids_intersection = filter_rupture_ids.for_parent_fault_ids(fault_ids, join_type=intersection_join)

    print(rupt_ids_intersection.tolist())

    assert rupt_ids_union != rupt_ids_intersection
    assert rupt_ids_union.issuperset(rupt_ids_intersection)
    print(fault_ids)


@pytest.mark.parametrize(
    "intersection_join", [None, 'intersplunk', SetOperationEnum.DIFFERENCE, SetOperationEnum.SYMMETRIC_DIFFERENCE, 45]
)
def test_ruptures_for_parent_fault_ids_unsupported_set_operation(crustal_solution_fixture, intersection_join):
    with pytest.raises((ValueError, KeyError)) as exc:
        _ = FilterRuptureIds(crustal_solution_fixture).for_parent_fault_ids([4, 5, 6], join_type=intersection_join)
    print(exc)


@pytest.mark.parametrize("intersection_join", ['intersection', SetOperationEnum.INTERSECTION])
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_fault_section_ids_set_operations(
    filter_subsection_ids, crustal_solution_fixture, drop_zero_rates, intersection_join
):

    subsection_ids = filter_subsection_ids.for_parent_fault_names(['Vernon 4', 'Alpine Jacksons to Kaniere']).tolist()
    print(subsection_ids)

    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    rupt_ids_union = filter_rupture_ids.for_subsection_ids(subsection_ids, join_type='union')
    rupt_ids_intersection = filter_rupture_ids.for_subsection_ids(subsection_ids, join_type=intersection_join)

    print(rupt_ids_intersection.tolist())
    print(rupt_ids_union.tolist())

    assert rupt_ids_union != rupt_ids_intersection
    assert rupt_ids_union.issuperset(rupt_ids_intersection)
    # assert 0


@pytest.mark.parametrize(
    "intersection_join", [None, 'intersplunk', SetOperationEnum.DIFFERENCE, SetOperationEnum.SYMMETRIC_DIFFERENCE, 45]
)
def test_ruptures_for_fault_section_ids_unsupported_set_operation(crustal_solution_fixture, intersection_join):
    with pytest.raises((ValueError, KeyError)) as exc:
        _ = FilterRuptureIds(crustal_solution_fixture).for_subsection_ids([4, 5, 6], join_type=intersection_join)
    print(exc)


@pytest.mark.parametrize("intersection_join", ['intersection', SetOperationEnum.INTERSECTION])
@pytest.mark.parametrize("drop_zero_rates", [False, True])
def test_ruptures_for_named_fault_names_set_operations(
    tiny_crustal_solution_fixture, crustal_solution_fixture, drop_zero_rates, intersection_join
):
    named_fault_names = ['Wellington: Wellington-Hutt Valley', 'Wairarapa']
    subsection_ids = (
        FilterSubsectionIds(tiny_crustal_solution_fixture).for_named_fault_names(named_fault_names).tolist()
    )
    print(subsection_ids)

    filter_rupture_ids = FilterRuptureIds(tiny_crustal_solution_fixture, drop_zero_rates=drop_zero_rates)

    rupt_ids_union = filter_rupture_ids.for_named_fault_names(named_fault_names, join_type='union')
    rupt_ids_intersection = filter_rupture_ids.for_named_fault_names(named_fault_names, join_type=intersection_join)

    print(rupt_ids_intersection.tolist())
    print(rupt_ids_union.tolist())

    assert rupt_ids_union != rupt_ids_intersection
    assert rupt_ids_union.issuperset(rupt_ids_intersection)


@pytest.mark.parametrize(
    "intersection_join", [None, 'intersplunk', SetOperationEnum.DIFFERENCE, SetOperationEnum.SYMMETRIC_DIFFERENCE, 45]
)
def test_ruptures_for_named_fault_names_unsupported_set_operation(tiny_crustal_solution_fixture, intersection_join):
    with pytest.raises((ValueError, KeyError)) as exc:
        _ = FilterRuptureIds(tiny_crustal_solution_fixture).for_named_fault_names(
            ['Wairarapa'], join_type=intersection_join
        )
    print(exc)


@pytest.mark.parametrize("intersection_join", ['intersection', SetOperationEnum.INTERSECTION])
@pytest.mark.parametrize("drop_zero_rates", [True, False])
def test_ruptures_for_parent_fault_names_set_operations(
    filter_parent_fault_ids, crustal_solution_fixture, drop_zero_rates, intersection_join
):
    filter_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=drop_zero_rates)
    fault_names = ['Vernon 4', 'Alpine Jacksons to Kaniere']
    # fault_ids = filter_parent_fault_ids.for_parent_fault_names().tolist()

    rupt_ids_union = filter_rupture_ids.for_parent_fault_names(fault_names, join_type='union')
    rupt_ids_intersection = filter_rupture_ids.for_parent_fault_names(fault_names, join_type=intersection_join)

    print(rupt_ids_intersection.tolist())
    assert rupt_ids_union != rupt_ids_intersection
    assert rupt_ids_union.issuperset(rupt_ids_intersection)


@pytest.mark.parametrize(
    "intersection_join", [None, 'intersplunk', SetOperationEnum.DIFFERENCE, SetOperationEnum.SYMMETRIC_DIFFERENCE, 45]
)
def test_ruptures_for_parent_fault_names_unsupported_set_operation(crustal_solution_fixture, intersection_join):
    with pytest.raises((ValueError, KeyError)) as exc:
        _ = FilterRuptureIds(crustal_solution_fixture).for_parent_fault_names(["$%^"], join_type=intersection_join)
    print(exc)
