import pytest

from solvis.fault_system_solution_helper import build_rupture_groups
from solvis.filter.rupture_id_filter import FilterRuptureIds


@pytest.mark.slow
def test_build_rupture_groups(composite_fixture):
    fss = composite_fixture._solutions['CRU']

    reps = list(build_rupture_groups(fss, min_overlap=0.5))
    assert len(reps) == 406
    assert reps[0] == {'rupture': 0, 'ruptures': [1, 2], 'sample_sections': 2}

    reps = list(build_rupture_groups(fss, min_overlap=0.8))
    assert len(reps) == 658
    assert reps[0] == {'rupture': 0, 'ruptures': [1], 'sample_sections': 2}


@pytest.mark.parametrize(
    "min_overlap, expected_len, sample_zero",
    [
        (0.5, 2, {'rupture': 0, 'ruptures': [1, 2], 'sample_sections': 2}),
        (0.8, 4, {'rupture': 0, 'ruptures': [1], 'sample_sections': 2}),
        (0.99, 5, {'rupture': 0, 'ruptures': [1], 'sample_sections': 2}),
    ],
)
def test_build_rupture_groups_fast(small_composite_fixture, min_overlap, expected_len, sample_zero):
    fss = small_composite_fixture._solutions['CRU']

    reps = list(build_rupture_groups(fss, min_overlap=min_overlap))
    assert len(reps) == expected_len
    assert reps[0] == sample_zero


@pytest.mark.parametrize(
    "min_overlap, expected_len, sample_zero",
    [
        (0.5, 1, {'rupture': 5, 'ruptures': [6, 7, 8, 9], 'sample_sections': 7}),
        (0.8, 1, {'rupture': 5, 'ruptures': [6, 7], 'sample_sections': 7}),
        (0.99, 2, {'rupture': 5, 'ruptures': [6], 'sample_sections': 7}),
    ],
)
def test_build_rupture_groups_filtered(small_composite_fixture, min_overlap, expected_len, sample_zero):
    fss = small_composite_fixture._solutions['CRU']

    m7less = list(FilterRuptureIds(fss).for_magnitude(max_mag=7.5))

    reps = list(build_rupture_groups(fss, rupture_ids=m7less, min_overlap=min_overlap))

    print(reps)

    assert len(reps) == expected_len
    assert reps[0] == sample_zero
