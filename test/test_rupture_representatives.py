from solvis.fault_system_solution_helper import build_rupture_groups


def test_build_rupture_groups(composite_fixture):
    fss = composite_fixture._solutions['CRU']

    for rep in build_rupture_groups(fss):
        print(rep)
    # assert 0
