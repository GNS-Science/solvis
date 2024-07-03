# define fixtures.py

import os
import pathlib
from copy import deepcopy
from itertools import chain

import nzshm_model as nm
import pytest

from solvis.inversion_solution import CompositeSolution
from solvis.inversion_solution.fault_system_solution import FaultSystemSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version("NSHM_v1.0.0")
slt = current_model.source_logic_tree
fslt = slt.fault_system_lts[0]  # PUY is used always, just for the 3 solution_ids

# assert fslt.short_name == "PUY-"

folder = pathlib.PurePath(os.path.realpath(__file__)).parent

ARCHIVES = dict(
    CRU="ModularAlpineVernonInversionSolution.zip",
    HIK="AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip",
    PUY="PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip",
    # PUY="PuysegurInversionSolutionMini.zip",
)

MINI_ARCHIVES = dict(
    PUY="PuysegurSmallSolution_compat.zip",
    HIK="HikurangiSmallSolution_compat.zip",
    CRU="CrustalSmallSolution_compat.zip",
)


@pytest.fixture(scope='module')
def archives():
    return ARCHIVES


@pytest.fixture(scope='module')
def small_archives():
    return MINI_ARCHIVES


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
        inversion_solution_id = FaultSystemSolution.get_branch_inversion_solution_id(branch)
        yield BranchInversionSolution.new_branch_solution(
            get_solution(inversion_solution_id, archive), branch, fslt.short_name, rupt_set_id
        )


@pytest.fixture(scope='class')
def small_composite_fixture():
    return build_composite_fixture(archives=MINI_ARCHIVES)


@pytest.fixture(scope='class')
def composite_fixture():
    return build_composite_fixture()


def build_composite_fixture(archives=ARCHIVES):

    # CBC This doesn't work now ??
    # fudge the model branches because we have too few fixtures
    for idx in [1, 2]:
        slt.fault_system_lts[idx].branches = deepcopy(slt.fault_system_lts[0].branches)

    composite = CompositeSolution(slt)  # create the new composite solutoin

    for fault_system_lt in slt.fault_system_lts:
        if fault_system_lt.short_name in ['PUY', 'CRU', 'HIK']:
            composite.add_fault_system_solution(
                fault_system_lt.short_name,
                FaultSystemSolution.from_branch_solutions(
                    branch_solutions(
                        fault_system_lt,
                        archive=archives[fault_system_lt.short_name],
                        rupt_set_id=f'rupset_{fault_system_lt.short_name}',
                    )
                ),
            )
    return composite


@pytest.fixture(scope='class')
def three_branch_solutions():
    return chain(
        branch_solutions(fslt, archive=ARCHIVES['PUY'], rupt_set_id='RUPTSET_ID'),
        branch_solutions(fslt, archive=ARCHIVES['HIK'], rupt_set_id='RUPTSET_ID'),
        branch_solutions(fslt, archive=ARCHIVES['CRU'], rupt_set_id='RUPTSET_ID'),
    )


@pytest.fixture(scope='class')
def three_small_branch_solutions():
    return chain(
        branch_solutions(fslt, archive=MINI_ARCHIVES['PUY'], rupt_set_id='RUPTSET_ID'),
        branch_solutions(fslt, archive=MINI_ARCHIVES['HIK'], rupt_set_id='RUPTSET_ID'),
        branch_solutions(fslt, archive=MINI_ARCHIVES['CRU'], rupt_set_id='RUPTSET_ID'),
    )


# PUY fixtures


@pytest.fixture(scope='module')
def puysegur_fixture(request):
    print("setup puysegur")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['PUY']))


@pytest.fixture(scope='module')
def puysegur_solution_fixture(request):
    print("setup puysegur")
    filename = pathlib.PurePath(folder, f"fixtures/{ARCHIVES['PUY']}")
    yield InversionSolution().from_archive(str(filename))


@pytest.fixture(scope='module')
def puy_branch_solutions():
    return branch_solutions(fslt, archive=ARCHIVES['PUY'], rupt_set_id='RUPTSET_ID')


@pytest.fixture(scope='module')
def puysegur_small_fixture(request):
    filename = pathlib.PurePath(folder, f"fixtures/{MINI_ARCHIVES['PUY']}")
    yield InversionSolution().from_archive(str(filename))


@pytest.fixture(scope='module')
def puysegur_small_fss_fixture(request):
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=MINI_ARCHIVES['PUY']))


# CRU fixtures


@pytest.fixture(scope='module')
def crustal_fixture(request):
    print("setup crustal")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['CRU']))


@pytest.fixture(scope='module')
def cru_branch_solutions():
    return branch_solutions(fslt, archive=ARCHIVES['CRU'], rupt_set_id='RUPTSET_ID')


@pytest.fixture(scope='class')
def crustal_solution_fixture(request):
    filename = pathlib.PurePath(folder, f"fixtures/{ARCHIVES['CRU']}")
    yield InversionSolution().from_archive(str(filename))


@pytest.fixture(scope='module')
def crustal_small_fss_fixture(request):
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=MINI_ARCHIVES['CRU']))


# HIK fixtures


@pytest.fixture(scope='module')
def hikurangi_fixture(request):
    print("setup hikurangi")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['HIK']))


@pytest.fixture(scope='module')
def hik_branch_solutions():
    return branch_solutions(fslt, archive=ARCHIVES['HIK'], rupt_set_id='RUPTSET_ID')


@pytest.fixture(scope='class')
def hikurangi_solution_fixture(request):
    filename = pathlib.PurePath(folder, f"fixtures/{MINI_ARCHIVES['HIK']}")
    yield InversionSolution().from_archive(str(filename))


@pytest.fixture(scope='module')
def hikurangi_small_fss_fixture(request):
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=MINI_ARCHIVES['HIK']))
