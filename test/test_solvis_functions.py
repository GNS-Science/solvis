import pandas as pd
import pytest

import solvis.solvis


def test_mfd_hist(crustal_small_fss_fixture, crustal_solution_fixture):

    mfd = solvis.solvis.mfd_hist(crustal_small_fss_fixture.ruptures_with_rupture_rates, "rate_weighted_mean")
    assert mfd.loc[pd.Interval(left=7.0, right=7.1)] == pytest.approx(0.0011956305)

    mfd = solvis.solvis.mfd_hist(crustal_solution_fixture.ruptures_with_rupture_rates)
    assert mfd.loc[pd.Interval(left=7.1, right=7.2)] == pytest.approx(0.0018980678)


# import solvis
import numpy as np

def test_ruptures_with_sum_of_section_participation(composite_fixture):

    fss = composite_fixture._solutions['CRU']

    print()
    print('fss.rs_with_rupture_rates')
    print( fss.rs_with_rupture_rates)

    # NB rate_weighted_mean is only available with fault_system_solution and NOT inversion_solution
    # with inversion solution we could use rupture_rate ??
    section_participation_df = fss.rs_with_rupture_rates\
        .pivot_table(values='rate_weighted_mean', index='section', aggfunc=np.sum)

    print('section_participation_df')
    print( section_participation_df)

    rupture_participation_df = fss.rupture_sections\
        .join(section_participation_df, on=fss.rupture_sections['section'])\
        .pivot_table(values='rate_weighted_mean', index='rupture', aggfunc=np.sum)\
        .rename(columns={"rate_weighted_mean":"cum_rate"})

    """
            cum_rate
    rupture
    0        0.000030
    1        0.000171
    2        0.000241
    3        0.000041
    4        0.000025
    ...           ...
    411265   0.008501
    411266   0.008621
    411267   0.008739
    411268   0.007671
    411269   0.012639

    [411270 rows x 1 columns]
    """

    hist = np.histogram(rupture_participation_df['cum_rate'], bins=30)

    """
    In [84]: np.histogram(rpd['cum_rate'])
    Out[84]:
    (array([196791,  33915,  16890,  19438,  20420,  18603,  20463,  35433,
             36006,  13311]),
     array([0.        , 0.02718008, 0.05436015, 0.08154023, 0.1087203 ,
            0.13590038, 0.16308045, 0.19026053, 0.2174406 , 0.24462068,
            0.27180076], dtype=float32))
    """

    print(hist)

    assert 0