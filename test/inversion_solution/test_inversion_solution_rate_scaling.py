#!python3 test_inversion_solution_rate_scaling.py

import pytest
from nzshm_common.location.location import location_by_id

from solvis import InversionSolution
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.geometry import circle_polygon


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

    rupture_ids = FilterRuptureIds(sol, drop_zero_rates=True).for_magnitude(max_mag=magnitude)
    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale, rupture_ids=list(rupture_ids))

    if magnitude < 5:
        # no ruptures below this magnitude (in inversion solutions), so no scaling should apply
        assert (
            new_sol.solution_file.rupture_rates["Annual Rate"].sum()
            == sol.solution_file.rupture_rates["Annual Rate"].sum()
        )
    elif magnitude > 9.5:
        # all ruptures should be below this magnitude, so we should scale everything
        assert (
            new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale
        ).sum() == sol.solution_file.rupture_rates["Annual Rate"].sum()
    else:
        # otherwise, scaling will be partial
        assert (new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale).sum() > sol.solution_file.rupture_rates[
            "Annual Rate"
        ].sum()


@pytest.mark.parametrize("scale", [0.1, 1.5])
@pytest.mark.parametrize("location", ['WLG', 'CHC', 'AKL'])
def test_scale_rupture_rates_for_polygon(crustal_solution_fixture, scale, location):

    sol = crustal_solution_fixture

    locn = location_by_id(location)

    polygon = circle_polygon(5e4, locn['latitude'], locn['longitude'])  # 50km circle around WLG
    rupture_ids = list(FilterRuptureIds(sol, drop_zero_rates=True).for_polygon(polygon))
    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale, rupture_ids=rupture_ids)

    # overall, the scaling will be partial
    new_sum_of_rates_check = (new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale).sum()
    old_sum_of_rates_check = sol.solution_file.rupture_rates["Annual Rate"].sum()
    if scale < 1.0:
        assert new_sum_of_rates_check > old_sum_of_rates_check
    else:
        assert new_sum_of_rates_check < old_sum_of_rates_check

    # but in target location, all rates must be scaled
    nrr = new_sol.solution_file.rupture_rates
    nrr_filter = nrr["Rupture Index"].isin(rupture_ids)

    orr = sol.solution_file.rupture_rates
    orr_filter = orr["Rupture Index"].isin(rupture_ids)

    assert (orr[orr_filter]["Annual Rate"] * scale).sum() == nrr[nrr_filter]["Annual Rate"].sum()


def test_scale_rupture_rates_for_all_rupture_ids(puysegur_small_fixture):

    sol = puysegur_small_fixture
    scale = 0.5

    rupture_ids = FilterRuptureIds(sol, drop_zero_rates=True).all()
    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale, rupture_ids=list(rupture_ids))

    # so everythong is scaled
    assert (new_sol.solution_file.rupture_rates["Annual Rate"] * 1 / scale).sum() == sol.solution_file.rupture_rates[
        "Annual Rate"
    ].sum()


def test_scale_rupture_rates_for_no_rupture_ids(puysegur_small_fixture):

    sol = puysegur_small_fixture
    scale = 0.5

    new_sol = InversionSolution.scale_rupture_rates(solution=sol, scale=scale, rupture_ids=[])

    # so nothing is scaled
    assert (new_sol.solution_file.rupture_rates["Annual Rate"]).sum() == sol.solution_file.rupture_rates[
        "Annual Rate"
    ].sum()
