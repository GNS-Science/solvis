import os
import pathlib

# import tempfile
from copy import deepcopy

import geopandas as gpd
import nzshm_model as nm
import pytest

# import solvis
from solvis import CompositeSolution, FaultSystemSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree()
fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids

ARCHIVES = dict(
    CRU="ModularAlpineVernonInversionSolution.zip",
    HIK="AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip",
    PUY="PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip",
)

FSR_COLUMNS_A = 27
FSR_COLUMNS_B = 26  # HIK
RATE_COLUMNS_A = 7


def get_solution(id: str, archive: str) -> InversionSolution:
    files = dict(
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ2=archive,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQz=archive,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ1=archive,
    )
    folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    filename = pathlib.PurePath(folder, f"fixtures/{files[id]}")
    return InversionSolution().from_archive(str(filename))


def branch_solutions(fslt, archive=ARCHIVES['CRU'], rupt_set_id='RUPTSET_ID'):
    for branch in fslt.branches:
        yield BranchInversionSolution.new_branch_solution(
            get_solution(branch.inversion_solution_id, archive), branch, fslt.short_name, rupt_set_id
        )


@pytest.fixture(scope='class')
def composite_fixture():

    # solutions = []

    v1_0_0 = nm.get_model_version('NSHM_1.0.0')
    slt = v1_0_0.source_logic_tree()
    print(slt.fault_system_branches[0])

    # fudge the model branches because we have too few fixtures
    for idx in [1, 2]:
        slt.fault_system_branches[idx].branches = deepcopy(slt.fault_system_branches[0].branches)

    composite = CompositeSolution()  # create the new composite solutoin
    for fault_system_lt in slt.fault_system_branches:
        if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
            composite.add_fault_system_solution(
                fault_system_lt.short_name,
                FaultSystemSolution.from_branch_solutions(
                    branch_solutions(
                        fault_system_lt,
                        archive=ARCHIVES[fault_system_lt.short_name],
                        rupt_set_id=f'rupset_{fault_system_lt.short_name}',
                    )
                ),
            )
    return composite


class TestThreeFaultSystems(object):
    def test_composite_rates_shape(self, composite_fixture):
        assert composite_fixture.rates.shape == (3101 + 15800 + 23675, RATE_COLUMNS_A)
        assert composite_fixture.composite_rates.shape == (127728, 6)

    @pytest.mark.TODO_check_values
    def test_rupture_surface(self, composite_fixture):
        surface = composite_fixture.rupture_surface('PUY', 42)
        assert surface.shape == (76, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_sections_with_rates_shape(self, composite_fixture):
        assert composite_fixture.fault_sections_with_rates.shape == (3858644, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_surfaces(self, composite_fixture):
        surfaces = composite_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (809, 15)
