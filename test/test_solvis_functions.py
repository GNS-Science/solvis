import pandas as pd
import pytest

import solvis.solvis


def test_mfd_hist(crustal_small_fss_fixture, crustal_solution_fixture):

    mfd = solvis.solvis.mfd_hist(crustal_small_fss_fixture.ruptures_with_rupture_rates, "rate_weighted_mean")
    assert mfd.loc[pd.Interval(left=7.0, right=7.1)] == pytest.approx(0.0011956305)

    mfd = solvis.solvis.mfd_hist(crustal_solution_fixture.ruptures_with_rupture_rates)
    assert mfd.loc[pd.Interval(left=7.1, right=7.2)] == pytest.approx(0.0018980678)
