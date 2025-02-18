#!python3 test_inversion_solution_rate_scaling.py

import pytest

from solvis import InversionSolution


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
def test_scale_rupture_rates_below_magniture(puysegur_small_fixture, magnitude):
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
