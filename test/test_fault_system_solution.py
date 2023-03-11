import os
import pathlib
import tempfile
from copy import deepcopy

import geopandas as gpd
import nzshm_model as nm
import pandas as pd
import pytest
from pandas.api.types import infer_dtype

import solvis
from solvis.inversion_solution.fault_system_solution import FaultSystemSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree()
fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids

ARCHIVES = dict(
    CRU="ModularAlpineVernonInversionSolution.zip",
    HIK="AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip",
    PUY="PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip",
    # PUY="PuysegurInversionSolutionMini.zip",
)

FSR_COLUMNS_A = 26
FSR_COLUMNS_B = 25  # HIK

RATE_COLUMNS_A = 6
COMPOSITE_RATE_COLUMNS = 6


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
def hikurangi_fixture(request):
    print("setup hikurangi")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['HIK']))


@pytest.fixture(scope='class')
def puysegur_fixture(request):
    print("setup puysegur")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['PUY']))


@pytest.fixture(scope='class')
def crustal_fixture(request):
    print("setup crustal")
    yield FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['CRU']))


def test_from_puy_branch_solutions():
    print(fslt.branches)
    composite = FaultSystemSolution.from_branch_solutions(branch_solutions(fslt, archive=ARCHIVES['PUY']))
    print(composite.fault_sections_with_rates)
    assert composite.fault_sections_with_rates.shape == (148394, FSR_COLUMNS_A)


class TestThreeFaultSystems(object):

    # @pytest.mark.skip('REVIEW')
    def test_composite_rates_shape(self):
        solutions = []

        v1_0_0 = nm.get_model_version('NSHM_1.0.0')
        slt = v1_0_0.source_logic_tree()
        print(slt.fault_system_branches[0])

        for idx in [1, 2]:
            slt.fault_system_branches[idx].branches = deepcopy(slt.fault_system_branches[0].branches)

        for fault_system_lt in slt.fault_system_branches:
            if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
                print('extending', fault_system_lt.short_name)
                solutions.extend(
                    branch_solutions(
                        fault_system_lt,
                        archive=ARCHIVES[fault_system_lt.short_name],
                        rupt_set_id=f'rupset_{fault_system_lt.short_name}',
                    )
                )

        # print('solutions', len(solutions))
        # print(solutions)
        # print()

        composite = FaultSystemSolution.from_branch_solutions(solutions)
        # print( composite.aggregate_rates.info() )
        # print( composite.aggregate_rates.head() )
        # print( composite.aggregate_rates.tail() )

        # assert composite.rates.shape == (3101 + 15800 + 23675, RATE_COLUMNS_A)
        assert composite.rates.shape == (4211, RATE_COLUMNS_A)
        assert composite.composite_rates.shape == (3 * 4211, COMPOSITE_RATE_COLUMNS)
        # assert composite.composite_rates.shape == (127728, COMPOSITE_RATE_COLUMNS)


class TestCrustal(object):
    def test_rates_shape(self, crustal_fixture):
        rates = crustal_fixture.rates
        assert rates.shape == (1006, RATE_COLUMNS_A)  # no 0 rates

    def test_check_indexes(self, crustal_fixture):
        sol = crustal_fixture
        assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index == sol.indices["Rupture Index"]

        # here we want a multi index
        # print( sol.rates.index.names )
        # assert sol.rates.index.names == ['fault_system', 'Rupture Index']

        print(sol.composite_rates.index.names)
        assert sol.composite_rates.index.names == ['solution_id', 'Rupture Index']

        assert sol.rates["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.indices["Rupture Index"].dtype == pd.UInt32Dtype()

    def test_check_types(self, crustal_fixture):
        sol = crustal_fixture
        assert isinstance(sol, FaultSystemSolution)
        assert sol.fault_regime == 'CRUSTAL'
        # assert sol.logic_tree_branch[0]['value']['enumName'] == "CRUSTAL"

        assert infer_dtype(sol.rates["fault_system"]) == "string"
        assert sol.rates["rate_weighted_mean"].dtype == 'float32'
        assert infer_dtype(sol.indices["Num Sections"]) == "integer"
        assert sol.indices["Num Sections"].dtype == pd.UInt16Dtype()
        assert sol.indices["# 1"].dtype == pd.UInt16Dtype()
        # assert 0


class TestDataFrames(object):
    def test_rates_shape(self, puysegur_fixture):
        sol = puysegur_fixture
        assert sol.rates.shape == (2033, RATE_COLUMNS_A)  # no 0 rates

    def test_rates_no_missing_aggregates(self, puysegur_fixture):
        sol = puysegur_fixture
        print(sol.rates.info())
        assert sol.rates["rate_weighted_mean"].count() == sol.rates.shape[0]
        print(sol.ruptures_with_rates.info())
        assert sol.ruptures_with_rates["rate_weighted_mean"].count() == sol.rates.shape[0]
        assert sol.ruptures_with_rates["rate_weighted_mean"].shape[0] == sol.rates.shape[0]
        # assert 0

    def test_ruptures_with_rates(self, puysegur_fixture):
        sol = puysegur_fixture
        print(sol.ruptures_with_rates.info())
        print()
        print(sol.ruptures_with_rates)
        assert sol.ruptures_with_rates.shape[0] == sol.rates.shape[0]

    def test_rs_with_rates(self, puysegur_fixture):
        sol = puysegur_fixture
        print(sol.rs_with_rates.info())
        print()
        print(sol.rs_with_rates)
        assert len(sol.rs_with_rates["Rupture Index"].unique()) == sol.rates.shape[0]

    def test_fault_sections_with_rates_shape(self, puysegur_fixture):
        sol = puysegur_fixture
        print(sol.fault_sections_with_rates.info())
        print()
        print(sol.fault_sections_with_rates)
        assert puysegur_fixture.fault_sections_with_rates.shape == (148394, FSR_COLUMNS_A)


class TestPuysegurSurfaces(object):
    def test_rupture_surface(self, puysegur_fixture):
        surface = puysegur_fixture.rupture_surface(3)
        print(surface.info())
        print()
        print(surface)
        assert surface.shape == (5, FSR_COLUMNS_A)
        # assert 0

    def test_fault_surfaces(self, puysegur_fixture):
        surfaces = puysegur_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (271, 14)


class TestHikurangi(object):
    def test_fault_sections_with_rates_shape(self, hikurangi_fixture):
        assert hikurangi_fixture.fault_sections_with_rates.shape == (42403, FSR_COLUMNS_B)

    def test_fault_surfaces(self, hikurangi_fixture):
        surfaces = hikurangi_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (452, 13)

    def test_rupture_surface(self, hikurangi_fixture):
        surface = hikurangi_fixture.rupture_surface(23660)
        assert surface.shape == (6, FSR_COLUMNS_B)

    def test_rates_shape(self, hikurangi_fixture):
        rates = hikurangi_fixture.rates
        assert rates.shape == (1172, RATE_COLUMNS_A)  # no 0 rates


class TestSerialisation(object):
    def test_write_to_archive_compatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        # ref_solution = next(branch_solutions(fslt, archive=ARCHIVES['CRU']))

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

        # assert not new_path.exists()
        # write the file
        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        assert new_path.exists()

    # @pytest.mark.skip('REVIEW read-write to compatible is not legit to compare rupture indices')
    def test_write_read_archive_compatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.rates)
        print(crustal_fixture.rates)
        assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
        assert read_sol.rates.shape == crustal_fixture.rates.shape
        # assert read_sol.rates['Rupture Index'].all() == crustal_fixture.rates['Rupture Index'].all()

    # @pytest.mark.skip('REVIEW read-write to compatible is not legit to compare rupture indices')
    def test_write_read_archive_compatible_composite_rates(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.composite_rates.info())
        print(read_sol.composite_rates.columns)
        print(read_sol.composite_rates)
        assert read_sol.composite_rates.columns.all() == crustal_fixture.composite_rates.columns.all()
        assert read_sol.composite_rates.shape == crustal_fixture.composite_rates.shape

    def test_write_read_archive_incompatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_incompatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=False)
        read_sol = solvis.FaultSystemSolution.from_archive(new_path)

        print(read_sol.rates)
        print(crustal_fixture.rates)
        assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
        # NO the composite solutions have diffent rate structure
        # assert read_sol.rates.shape == crustal_fixture.rates.shape
        assert read_sol.rates['Rupture Index'].all() == crustal_fixture.rates['Rupture Index'].all()

    # def test_write_read_archive_filtered_incompatible(self, crustal_fixture):

    #     folder = tempfile.TemporaryDirectory()
    #     # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    #     new_path = pathlib.Path(folder.name, 'test_incompatible_filtered_archive.zip')

    #     fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
    #     ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

    #     rr = crustal_fixture.rates
    #     ruptures = rr[rr['rate_mean'] > 1e-6]["Rupture Index"].unique()
    #     print(ruptures)
    #     new_sol = solvis.FaultSystemSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=False)
    #     read_sol = solvis.FaultSystemSolution.from_archive(new_path)

    #     print(read_sol.rates)
    #     print(crustal_fixture.rates)
    #     # assert read_sol.rates['Rupture Index'].all() == crustal_fixture.rates['Rupture Index'].all()

    #     assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
    #     assert read_sol.rates.shape[1] == crustal_fixture.rates.shape[1]

    #     assert read_sol.indices.shape[0] == len(ruptures)
    #     assert read_sol.rates.shape[0] == len(ruptures)
    #     assert read_sol.ruptures.shape[0] == len(ruptures)

    # def test_write_read_archive_filtered_compatible(self, crustal_fixture):

    #     folder = tempfile.TemporaryDirectory()
    #     # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    #     new_path = pathlib.Path(folder.name, 'test_compatible_filtered_archive.zip')

    #     fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
    #     ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

    #     rr = crustal_fixture.rates
    #     ruptures = rr[rr['rate_mean'] > 1e-6]["Rupture Index"].unique()
    #     print(ruptures)
    #     new_sol = solvis.FaultSystemSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=True)
    #     read_sol = solvis.FaultSystemSolution.from_archive(new_path)

    #     print(read_sol.rates)
    #     print(crustal_fixture.rates)

    #     assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
    #     assert read_sol.rates.shape[1] == crustal_fixture.rates.shape[1]

    #     assert read_sol.indices.shape[0] == len(ruptures)
    #     assert read_sol.rates.shape[0] == len(ruptures)
    #     assert read_sol.ruptures.shape[0] == len(ruptures)
