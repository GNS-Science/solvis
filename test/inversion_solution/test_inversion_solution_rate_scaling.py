#!python3 test_inversion_solution_rate_scaling.py

import pytest
from nzshm_common.location.location import location_by_id

from solvis import InversionSolution, circle_polygon
from solvis.filter.rupture_id_filter import FilterRuptureIds


@pytest.mark.parametrize("scale", [0.1, 0.55, 0.89, 1.5])
def test_scale_rupture_rates_uniformly(puysegur_small_fixture, scale):
    sol = puysegur_small_fixture
    # scale = 0.5
    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale)

    # print(sol.solution_file.rupture_rates.head())
    # print()
    # print(new_sol.solution_file.rupture_rates.head())

    assert (new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale).sum() == sol.solution_file.rupture_rates[
        "Annual Rate"
    ].sum()


@pytest.mark.parametrize("magnitude", [1.5, 4.2, 6.5, 7.25, 9.55])
def test_scale_rupture_rates_below_magnitude(puysegur_small_fixture, magnitude):
    sol = puysegur_small_fixture
    scale = 0.5
    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale, max_magnitude=magnitude)

    # print(sol.solution_file.rupture_rates.head())
    # print()
    # print(new_sol.solution_file.rupture_rates.head())

    if magnitude < 5:
        # no rates should be below this magniture, so no scaling should apply
        assert (
            new_sol.solution_file.rupture_rates["Annual Rate"].sum()
            == sol.solution_file.rupture_rates["Annual Rate"].sum()
        )
    elif magnitude < 9.5:
        # scaling will be partial
        assert (new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale).sum() > sol.solution_file.rupture_rates[
            "Annual Rate"
        ].sum()
    else:
        # all ruptures should be below this magnitude, so we should scale everything
        assert (
            new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale
        ).sum() == sol.solution_file.rupture_rates["Annual Rate"].sum()


@pytest.mark.skip('WIP')
def test_scale_rupture_rates_for_polygon(crustal_solution_fixture):

    WLG = location_by_id('WLG')
    polygon = circle_polygon(5e4, WLG['latitude'], WLG['longitude'])  # 50km circle around WLG
    rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).for_polygon(polygon)
    all_rupture_ids = FilterRuptureIds(crustal_solution_fixture, drop_zero_rates=False).all()

    assert all_rupture_ids.issuperset(rupture_ids)

    # TODO: added test coverage and implmenent the feature
    assert 0
