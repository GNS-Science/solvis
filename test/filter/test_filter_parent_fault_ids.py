import random

from solvis.filter.parent_fault_id_filter import FilterParentFaultIds, parent_fault_name_id_mapping


def test_parent_fault_names_all(filter_parent_fault_ids, crustal_solution_fixture):
    all_fault_ids = filter_parent_fault_ids.all()
    print(list(all_fault_ids))
    assert len(all_fault_ids) == len(crustal_solution_fixture.solution_file.fault_sections['ParentID'].unique())


def test_filter_inversion_solution_or_model(crustal_solution_fixture):
    rupts_a = FilterParentFaultIds(crustal_solution_fixture).all()
    rupts_b = FilterParentFaultIds(crustal_solution_fixture.model).all()
    assert rupts_a == rupts_b


def test_filter_fault_system_solution_or_model(crustal_small_fss_fixture):
    rupts_a = FilterParentFaultIds(crustal_small_fss_fixture).all()
    rupts_b = FilterParentFaultIds(crustal_small_fss_fixture.model).all()
    assert rupts_a == rupts_b


def test_fault_names_as_ids(filter_parent_fault_ids):
    assert filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere']) == set([23])
    assert filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere', 'Vernon 4']) == set([23, 585])


def test_parent_fault_ids(filter_parent_fault_ids):
    assert filter_parent_fault_ids.for_parent_fault_names(['Vernon 4']) == set([585])


def test_parent_fault_subsection_ids(filter_parent_fault_ids, filter_subsection_ids):
    pids = filter_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere'])
    subsections = filter_subsection_ids.for_parent_fault_ids(pids)
    print(pids)
    print(subsections)
    assert filter_parent_fault_ids.for_subsection_ids(subsections) == pids


def test_parent_fault_name_id_mapping(filter_parent_fault_ids, crustal_solution_fixture):
    parent_ids = list(filter_parent_fault_ids.for_parent_fault_names(['Vernon 4']))
    mapping = list(parent_fault_name_id_mapping(crustal_solution_fixture, parent_ids))

    print(parent_ids)
    print(mapping)
    assert len(mapping) == 1
    assert mapping[0].parent_id == 585
    assert mapping[0].parent_fault_name == 'Vernon 4'


def test_round_trip_ids_and_names(filter_parent_fault_ids, crustal_solution_fixture):
    pnames = random.sample(crustal_solution_fixture.model.parent_fault_names, 3)
    parent_ids = list(filter_parent_fault_ids.for_parent_fault_names(pnames))
    print(pnames)
    print(parent_ids)

    mapping = list(parent_fault_name_id_mapping(crustal_solution_fixture, parent_ids))
    print(mapping)

    for parent in mapping:
        assert filter_parent_fault_ids.for_parent_fault_names([parent.parent_fault_name]) == set([parent.parent_id])


def test_parent_faults_for_ruptures(filter_parent_fault_ids, filter_rupture_ids, crustal_solution_fixture):
    # pnames = ['Alpine Jacksons to Kaniere'] # small crustal_solution_fixture has rupture on only one parent
    pnames = random.sample(crustal_solution_fixture.model.parent_fault_names, 2)

    pids = filter_parent_fault_ids.for_parent_fault_names(pnames)
    rupt_ids = list(filter_rupture_ids.for_parent_fault_names(pnames))

    # at least one of ruptures parents must be one of the original parents
    rupt_sample = random.sample(rupt_ids, 3)
    assert filter_parent_fault_ids.for_rupture_ids(rupt_sample).intersection(pids)

    # there will be more parent faults, given all those ruptures on the original parents
    assert filter_parent_fault_ids.for_rupture_ids(rupt_ids).issuperset(pids)


def test_parent_faults_filter_chaining(filter_parent_fault_ids, crustal_solution_fixture):
    # filter_rupture_ids = FilterParentFaultIds(crustal_solution_fixture)
    pnames = random.sample(crustal_solution_fixture.model.parent_fault_names, 2)

    together = filter_parent_fault_ids.for_parent_fault_names(pnames)
    first = filter_parent_fault_ids.for_parent_fault_names(pnames[:1])
    second = filter_parent_fault_ids.for_parent_fault_names(pnames[1:])

    assert together.difference(second) == first
    assert together.difference(first) == second

    ## union
    chained = filter_parent_fault_ids.for_parent_fault_names(pnames[:1]).for_parent_fault_names(
        pnames[1:], join_prior='union'
    )
    assert together == chained

    ## difference
    diff = filter_parent_fault_ids.for_parent_fault_names(pnames).for_parent_fault_names(
        pnames[1:], join_prior='difference'
    )
    assert diff == second.difference(together)

    ## symmetric_differnce
    diff = filter_parent_fault_ids.for_parent_fault_names(pnames).for_parent_fault_names(
        pnames[1:], join_prior='symmetric_difference'
    )
    assert diff == second.symmetric_difference(together)

    ## intersection
    intersect = filter_parent_fault_ids.for_parent_fault_names(pnames).for_parent_fault_names(
        pnames[1:]
    )  # default join_prior is `intersection`
    assert intersect == second


def test_parent_faults_for_named_faults(filter_parent_fault_ids, crustal_solution_fixture):
    named_fault = 'Ostler'
    pids = filter_parent_fault_ids.for_named_fault_names([named_fault])
    assert list(pids) == [334, 335]
