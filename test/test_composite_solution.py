import os
import pathlib
import tempfile

import geopandas as gpd
import nzshm_model as nm
import pytest

import solvis
from solvis.inversion_solution.composite_solution import CompositeSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree()
fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids

CRU_ARCHIVE = "ModularAlpineVernonInversionSolution.zip"
HIK_ARCHIVE = "AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
PUY_ARCHIVE = "PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip"


def get_solution(id: str, archive: str) -> InversionSolution:
    files = dict(
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ2=archive,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQz=archive,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ1=archive,
    )
    folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    filename = pathlib.PurePath(folder, f"fixtures/{files[id]}")
    return InversionSolution().from_archive(str(filename))


def branch_solutions(fslt, archive=CRU_ARCHIVE):
    for branch in fslt.branches:
        yield BranchInversionSolution.new_branch_solution(
            get_solution(branch.inversion_solution_id, archive),
            branch, fslt.short_name, 'RUPTSET_ID')

@pytest.fixture(scope='class')
def hikurangi_fixture(request):
    print("setup hikurangi")
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=HIK_ARCHIVE))


@pytest.fixture(scope='class')
def puysegur_fixture(request):
    print("setup puysegur")
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=PUY_ARCHIVE))


@pytest.fixture(scope='class')
def crustal_fixture(request):
    print("setup crustal")
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=CRU_ARCHIVE))


def test_from_puy_branch_solutions():
    print(fslt.branches)
    composite = CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=PUY_ARCHIVE))
    print(composite.fault_sections_with_rates)
    assert composite.fault_sections_with_rates.shape == (1369370, 26)


class TestCrustal(object):
    def test_rates_shape(self, crustal_fixture):
        rates = crustal_fixture.rates
        assert rates.shape == (3101, 6)


class TestPuysegur(object):
    def test_rates_shape(self, puysegur_fixture):
        rates = puysegur_fixture.rates
        assert rates.shape == (15800, 6)

    def test_rupture_surface(self, puysegur_fixture):
        surface = puysegur_fixture.rupture_surface(42)
        assert surface.shape == (76, 26)

    def test_fault_sections_with_rates_shape(self, puysegur_fixture):
        assert puysegur_fixture.fault_sections_with_rates.shape == (1369370, 26)

    def test_fault_surfaces(self, puysegur_fixture):
        surfaces = puysegur_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (271, 14)


class TestHikurangi(object):
    def test_fault_sections_with_rates_shape(self, hikurangi_fixture):
        assert hikurangi_fixture.fault_sections_with_rates.shape == (2398024, 25)

    def test_fault_surfaces(self, hikurangi_fixture):
        surfaces = hikurangi_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (452, 13)

    def test_rupture_surface(self, hikurangi_fixture):
        surface = hikurangi_fixture.rupture_surface(44)
        assert surface.shape == (94, 25)

    def test_rates_shape(self, hikurangi_fixture):
        rates = hikurangi_fixture.rates
        assert rates.shape == (23675, 6)


class TestSerialisation(object):
    def test_write_to_archive_compatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        # ref_solution = next(branch_solutions(fslt, archive=CRU_ARCHIVE))

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

        # assert not new_path.exists()
        # write the file
        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        assert new_path.exists()

    def test_write_read_archive_compatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.CompositeSolution.from_archive(new_path)

        print(read_sol.rates)
        print(crustal_fixture.rates)
        assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
        assert read_sol.rates.shape == crustal_fixture.rates.shape
        assert read_sol.rates['Rupture Index'].all() == crustal_fixture.rates['Rupture Index'].all()


    def test_write_read_archive_compatible_composite_rates(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_compatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=True)
        read_sol = solvis.CompositeSolution.from_archive(new_path)

        print(read_sol.composite_rates.info())
        print(read_sol.composite_rates.columns)
        print(read_sol.composite_rates)
        assert read_sol.composite_rates.columns.all() == crustal_fixture.composite_rates.columns.all()
        assert read_sol.composite_rates.shape == crustal_fixture.composite_rates.shape
        assert read_sol.composite_rates['Rupture Index'].all() == crustal_fixture.composite_rates['Rupture Index'].all()


    def test_write_read_archive_incompatible(self, crustal_fixture):

        folder = tempfile.TemporaryDirectory()
        # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
        new_path = pathlib.Path(folder.name, 'test_incompatible_archive.zip')

        fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
        ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

        crustal_fixture.to_archive(str(new_path), ref_solution, compat=False)
        read_sol = solvis.CompositeSolution.from_archive(new_path)

        print(read_sol.rates)
        print(crustal_fixture.rates)
        assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
        assert read_sol.rates.shape == crustal_fixture.rates.shape
        assert read_sol.rates['Rupture Index'].all() == crustal_fixture.rates['Rupture Index'].all()

    # def test_write_read_archive_filtered_incompatible(self, crustal_fixture):

    #     folder = tempfile.TemporaryDirectory()
    #     # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    #     new_path = pathlib.Path(folder.name, 'test_incompatible_filtered_archive.zip')

    #     fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
    #     ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

    #     rr = crustal_fixture.rates
    #     ruptures = rr[rr['rate_mean'] > 1e-6]["Rupture Index"].unique()
    #     print(ruptures)
    #     new_sol = solvis.CompositeSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=False)
    #     read_sol = solvis.CompositeSolution.from_archive(new_path)

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
    #     new_sol = solvis.CompositeSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=True)
    #     read_sol = solvis.CompositeSolution.from_archive(new_path)

    #     print(read_sol.rates)
    #     print(crustal_fixture.rates)

    #     assert read_sol.rates.columns.all() == crustal_fixture.rates.columns.all()
    #     assert read_sol.rates.shape[1] == crustal_fixture.rates.shape[1]

    #     assert read_sol.indices.shape[0] == len(ruptures)
    #     assert read_sol.rates.shape[0] == len(ruptures)
    #     assert read_sol.ruptures.shape[0] == len(ruptures)
