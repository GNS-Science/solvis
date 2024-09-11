import random

from solvis.filter.parent_fault_id_filter import parent_fault_name_id_mapping


def test_parent_fault_names_all(filter_parent_fault_ids, fss):
    all_fault_ids = filter_parent_fault_ids.all()
    print(list(all_fault_ids))
    assert len(all_fault_ids) == len(fss.fault_sections['ParentID'].unique())


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


def test_parent_fault_name_id_mapping(filter_parent_fault_ids, fss):
    parent_ids = list(filter_parent_fault_ids.for_parent_fault_names(['Vernon 4']))
    mapping = list(parent_fault_name_id_mapping(fss, parent_ids))

    print(parent_ids)
    print(mapping)
    assert len(mapping) == 1
    assert mapping[0].id == 585
    assert mapping[0].parent_fault_name == 'Vernon 4'


def test_round_trip_ids_and_names(filter_parent_fault_ids, fss):
    pnames = random.sample(fss.parent_fault_names, 3)
    parent_ids = list(filter_parent_fault_ids.for_parent_fault_names(pnames))
    print(pnames)
    print(parent_ids)

    mapping = list(parent_fault_name_id_mapping(fss, parent_ids))
    print(mapping)

    for parent in mapping:
        assert filter_parent_fault_ids.for_parent_fault_names([parent.parent_fault_name]) == set([parent.id])


def test_parent_faults_for_ruptures(filter_parent_fault_ids, filter_rupture_ids, fss):
    pnames = random.sample(fss.parent_fault_names, 2)
    pids = filter_parent_fault_ids.for_parent_fault_names(pnames)
    rupt_ids = list(filter_rupture_ids.for_parent_fault_names(pnames))

    # at least one of ruptures parents must be one of the original parents
    rupt_sample = random.sample(rupt_ids, 3)
    assert filter_parent_fault_ids.for_rupture_ids(rupt_sample).intersection(pids)

    # there will be more parent faults, given all those ruptures on the original parents
    assert filter_parent_fault_ids.for_rupture_ids(rupt_ids).issuperset(pids)
