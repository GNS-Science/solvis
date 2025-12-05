import pandas as pd
import pytest

import solvis.utils


def test_mfd_hist(crustal_small_fss_fixture, crustal_solution_fixture):
    mfd = solvis.utils.mfd_hist(crustal_small_fss_fixture.model.ruptures_with_rupture_rates, "rate_weighted_mean")
    assert mfd.loc[pd.Interval(left=7.0, right=7.1)] == pytest.approx(0.0011956305)

    mfd = solvis.utils.mfd_hist(crustal_solution_fixture.model.ruptures_with_rupture_rates)
    assert mfd.loc[pd.Interval(left=7.1, right=7.2)] == pytest.approx(0.0018980678)
