import os
import pathlib

import geopandas as gpd
import nzshm_model as nm
import pytest

import solvis
from solvis.inversion_solution.composite_solution import CompositeSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree()

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
        yield BranchInversionSolution.new_branch_solution(get_solution(branch.inversion_solution_id, archive), branch)


@pytest.fixture(scope='class')
def hikurangi_fixture(request):
    print("setup hikurangi")
    fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=HIK_ARCHIVE))


@pytest.fixture(scope='class')
def puysegur_fixture(request):
    print("setup puysegur")
    fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=PUY_ARCHIVE))


@pytest.fixture(scope='class')
def crustal_fixture(request):
    print("setup crustal")
    fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids
    yield CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=CRU_ARCHIVE))


def test_from_puy_branch_solutions():
    fslt = slt.fault_system_branches[0]  # PUY is used always , just for the 3 solution_ids
    print(fslt.branches)
    composite = CompositeSolution.from_branch_solutions(branch_solutions(fslt, archive=PUY_ARCHIVE))
    assert composite.fault_sections_with_rates.shape == (1369370, 24)


class TestCrustal(object):
    def test_rates_shape(self, crustal_fixture):
        rates = crustal_fixture.rates
        assert rates.shape == (1006, 4)


class TestPuysegur(object):
    def test_rates_shape(self, puysegur_fixture):
        rates = puysegur_fixture.rates
        assert rates.shape == (2033, 4)

    def test_rupture_surface(self, puysegur_fixture):
        surface = puysegur_fixture.rupture_surface(42)
        assert surface.shape == (76, 24)

    def test_fault_sections_with_rates_shape(self, puysegur_fixture):
        assert puysegur_fixture.fault_sections_with_rates.shape == (1369370, 24)

    def test_fault_surfaces(self, puysegur_fixture):
        surfaces = puysegur_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (271, 14)


class TestHikurangi(object):
    def test_fault_sections_with_rates_shape(self, hikurangi_fixture):
        assert hikurangi_fixture.fault_sections_with_rates.shape == (2398024, 23)

    def test_fault_surfaces(self, hikurangi_fixture):
        surfaces = hikurangi_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (452, 13)

    def test_rupture_surface(self, hikurangi_fixture):
        surface = hikurangi_fixture.rupture_surface(44)
        assert surface.shape == (94, 23)

    def test_rates_shape(self, hikurangi_fixture):
        rates = hikurangi_fixture.rates
        assert rates.shape == (1172, 4)


if __name__ == "__main__":
    fslt = slt.fault_system_branches[0]  # PUY
    print(fslt.branches)

    # df0 = build_rates(branch_solutions(fslt))
    # print(df0.info())
    # print()
    # print(df0)

    composite = CompositeSolution.from_branch_solutions(branch_solutions(fslt))

    # print("")
    # print('rates')
    # print(composite.rates.info())
    # print(composite.rates.head())
    # print("")
    # print('ruptures_with_rates')
    # print(composite.ruptures_with_rates.info())
    # print(composite.ruptures_with_rates.head())

    rupt_surface_df = composite.rupture_surface(3)
    print(rupt_surface_df)

    solvis.export_geojson(composite.fault_surfaces(), "puysegur_composite_surfaces.geojson", indent=2)

    print()
    print(rupt_surface_df.to_json())
    # solvis.export_geojson(composite.rupture_surface(3), f"puysegur_composite_rupture3.geojson", indent=2)
