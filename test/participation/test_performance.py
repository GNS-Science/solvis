import os
import pathlib
import time

import pytest

import solvis
from solvis.filter import FilterRuptureIds, FilterSubsectionIds
from solvis.solution import SolutionParticipation

folder = pathlib.Path(os.path.realpath(__file__)).parent

single_sol = folder.parent / "fixtures" / "TinyInversionSolution" / "TinyInversionSolution.zip"

print(single_sol.absolute())
assert single_sol.exists()

TARGET_FAULTS = ['Masterton', 'Ohariu']


def faster_subsection_filter(solution, subsection_ids):
    # https://stackoverflow.com/questions/67456315/a-faster-way-than-the-isin-function-of-pandas-to-extract-conditional-rows
    df0 = solution.model.rs_with_rupture_rates.copy()
    df0.section = df0.section.astype('int32')
    # print(f'df0 copy/dtype took : {t1-t0} seconds')

    df0 = df0.set_index('section')
    # df0 = df0.sort_index()
    # ssids = np.array(subsection_ids, dtype='int32')
    return df0.loc[subsection_ids]


def original_subsection_filter(solution, subsection_ids):
    # SLOW!!!!
    df0 = solution.rs_with_rupture_rates.copy()
    df0 = df0[df0["section"].isin(subsection_ids)]
    # print(f'apply section filter took : {t1-t0} seconds')
    return df0


def original_rupture_filter(solution, rids):
    df0 = solution.model.rs_with_rupture_rates.copy()
    df0 = df0[df0["Rupture Index"].isin(rids)]
    return df0


def faster_rupture_filter(solution, rids):
    df0 = solution.model.rs_with_rupture_rates.copy()
    # df0.section = df0.section.astype('int32')
    # print(f'df0 copy/dtype took : {t1-t0} seconds')
    df0 = df0.set_index('Rupture Index')
    # ssids = np.array(subsection_ids, dtype='int32')
    return df0.loc[rids]


def faster_combo_filter(df0, subsection_ids, rids):
    df0 = df0.set_index('section')
    df0 = df0.loc[subsection_ids]
    df0 = df0.reset_index().set_index('Rupture Index')
    df0 = df0.loc[rids]
    return df0


def current_combo_filter(df0, subsection_ids, rids):
    df0 = df0[df0['section'].isin(subsection_ids)]
    df0 = df0[df0["Rupture Index"].isin(rids)]
    return df0


def slower_query_filter(df0, subsection_ids, rids):
    df0 = df0.set_index('section')
    df0 = df0.query(f"section in {subsection_ids}")
    df0 = df0.reset_index().set_index('Rupture Index')
    df0 = df0.query(f"'Rupture Index' in {rids}")
    return df0


# @pytest.mark.skip('section' dtype=float64) was the root problem')
@pytest.mark.skip(
    reason="performance tests no longer pass as expected, changes in dependencies may have changed performance"
)
def test_combo_filtering_options():
    solution = solvis.InversionSolution.from_archive(single_sol)

    # this is needed so the property is cached for both timing tests
    df0 = solution.model.rs_with_rupture_rates.copy()  # property
    rids = list(FilterRuptureIds(solution).for_parent_fault_names(TARGET_FAULTS))
    subsection_ids = FilterSubsectionIds(solution).for_rupture_ids(rids)

    t0 = time.perf_counter()
    fs0 = faster_combo_filter(df0, subsection_ids, rids)
    t1 = time.perf_counter()
    print(f'faster combo filter .loc took : {t1-t0} seconds')
    # print(fs0.info())
    print()

    t2 = time.perf_counter()
    fs1 = current_combo_filter(df0, subsection_ids, rids)
    t3 = time.perf_counter()
    print(f'current combo filter took : {t3-t2} seconds')
    # print(fs1.info())
    print()

    # t4 = time.perf_counter()
    # fs2 = slower_query_filter(df0, subsection_ids, rids)
    # t5 = time.perf_counter()
    # print(f'slower_query_filter took : {t5-t4} seconds')
    # print(fs2.info())
    # print()

    # assert t3-t2 > (t1-t0) * 2.5

    # Is timing in the aggregation phase affected??

    # original_rates = solution.section_participation_rates(subsection_ids, rids)
    t10 = time.perf_counter()
    old_rates = fs1.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    # t11 = time.perf_counter()
    # slow_query_rates = fs2.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    t12 = time.perf_counter()
    new_rates = fs0.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    t13 = time.perf_counter()

    print(f'aggregate old: {t12-t10}')
    print(f'aggregate faster (reindex/.loc): {t13-t12}')
    # print(f'aggregate slower (query): {t12-t11}')

    # assert old_rates["Annual Rate"].all() == slow_query_rates["Annual Rate"].all()
    assert old_rates["Annual Rate"].all() == new_rates["Annual Rate"].all()

    # new way MUST be faster * 2.5
    assert (t13 - t12) < (t12 - t10)  # aggregration
    # assert (t3-t2) > (t1-t0) * 2.5  # filtering
    # assert 0

    print(fs1.info())
    """
    WITH sections dtype: 'Int32'
    ============================
    faster combo filter .loc took : 1.409240401815623 seconds
    current combo filter took : 0.4251648848876357 seconds

    aggregate old: 0.00187242915853858
    aggregate faster (reindex/.loc): 0.0015068971551954746
    """

    """
    WITH sections dtype: 'float64'
    ============================
    faster combo filter .loc took : 1.2579642031341791 seconds
    current combo filter took : 4.538873607758433 seconds

    aggregate old: 0.0017163190059363842
    aggregate faster (reindex/.loc): 0.0013540848158299923
    """
    """
    WITH sections dtype: 'UInt32'
    ============================
    faster combo filter .loc took : 1.2095669759437442 seconds
    current combo filter took : 2.8522064238786697 seconds

    aggregate old: 0.0017591239884495735
    aggregate faster (reindex/.loc): 0.0015026167966425419
    """
    # assert 0


def test_rupture_filtering_options():
    solution = solvis.InversionSolution.from_archive(single_sol)

    # this is needed so the property is cached for both timing tests
    df0 = solution.model.rs_with_rupture_rates  # noqa

    rids = list(FilterRuptureIds(solution).for_parent_fault_names(TARGET_FAULTS))

    t0 = time.perf_counter()
    fs0 = faster_rupture_filter(solution, rids)
    t1 = time.perf_counter()
    print(f'fastest rupture filter .loc took : {t1-t0} seconds')
    print(fs0)
    print()

    t2 = time.perf_counter()
    fs1 = original_rupture_filter(solution, rids)
    t3 = time.perf_counter()

    print(f'current rupture filter .loc took : {t3-t2} seconds')
    print(fs1)
    print()

    # new way MUST be faster * 2.5
    # assert t3 - t2 > (t1 - t0) * 2.5
    old_rates = fs1.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    # print(old_rates)

    new_rates = fs0.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    # print(new_rates)
    assert old_rates["Annual Rate"].all() == new_rates["Annual Rate"].all()
    # assert 0


@pytest.mark.skip('section dtype (float) was the root problem')
def test_subsection_filtering_options():

    solution = solvis.InversionSolution.from_archive(single_sol)

    # this is needed so the property is cached for both timing tests
    df0 = solution.model.rs_with_rupture_rates  # noqa

    subsection_ids = [53, 54, 55, 56, 57, 58, 2219, 2218, 2220, 2102, 2103]

    t0 = time.perf_counter()
    fs0 = faster_subsection_filter(solution, subsection_ids)
    t1 = time.perf_counter()
    print(f'fastest section filter .loc took : {t1-t0} seconds')
    print(fs0)
    print()

    t2 = time.perf_counter()
    fs1 = original_subsection_filter(solution, subsection_ids)
    t3 = time.perf_counter()

    print(f'current section filter .loc took : {t3-t2} seconds')
    print(fs1)
    print()

    # new way MUST be faster * 2.5
    assert (t3 - t2) > (t1 - t0) * 2.5

    old_rates = fs1.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    # print(old_rates)

    new_rates = fs0.pivot_table(values="Annual Rate", index=['section'], aggfunc='sum')
    # print(new_rates)

    assert old_rates["Annual Rate"].all() == new_rates["Annual Rate"].all()


# @pytest.mark.performance
def test_section_performance():
    solution = solvis.InversionSolution.from_archive(single_sol)

    # RATE_COLUMN = "Annual Rate"
    # this is needed so the property is cached for both timing tests
    df0 = solution.model.rs_with_rupture_rates.copy()  # noqa

    def process_1(solution):

        t0 = time.perf_counter()

        ruptures = FilterRuptureIds(solution).for_parent_fault_names(TARGET_FAULTS)
        # .for_magnitude(5, 8.2)

        t01 = time.perf_counter()
        print(f'filter ruptures took {t01-t0} seconds')

        # # get rupture fault sections (rs) with rates for those ruptures
        # df0 = solution.model.rs_with_rupture_rates

        # rupture_sections_df = df0[df0["Rupture Index"].isin(ruptures)]
        # rupture_ids = list(rupture_sections_df["Rupture Index"].unique())

        # print(f' {len(ruptures)} unique ruptures...')
        # print(f"rupture_sections_df shape: {rupture_sections_df.shape}")

        # t1 = time.perf_counter()
        # print(f'rupture_sections_df took {t1-t0} seconds')

        return ruptures

    def process_2(solution, rupture_ids):
        t1 = time.perf_counter()

        subsection_ids = FilterSubsectionIds(solution).for_rupture_ids(rupture_ids)
        print(f' {len(subsection_ids)} rupture subsections...')

        print(f'rupture subsections: {len(subsection_ids)}')

        t2 = time.perf_counter()
        print(f'filter rupture subsections took : {t2-t1} seconds')

        section_rates = SolutionParticipation(solution).section_participation_rates(
            list(subsection_ids)
        )  # , list(rupture_ids))

        t3 = time.perf_counter()
        print(f'section rates took {t3-t2} seconds')
        print(f"section_rates shape: {section_rates.shape}")

    for _pass in range(2):
        print(f'pass: 1.{_pass}')
        print('===========')

        rupture_ids = process_1(solution)
        print()

    print(list(rupture_ids))

    for _pass in range(1):
        print(f'pass: 2.{_pass}')
        print('===========')

        process_2(solution, rupture_ids)
        print()

    # assert 0
    """
     21 unique ruptures...
    rupture_sections_df shape: (666, 8)
    rupture_sections_df took 11.17839854164049 seconds
    rupture subsections: 179
    filter rupture subsections took : 0.10153115028515458 seconds
    section rates took 7.005476752761751 seconds
    section_rates shape: (179, 1)
    """
