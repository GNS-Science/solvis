import geopandas as gpd
import nzshm_model as nm
import pandas as pd
import pytest
from pandas.api.types import infer_dtype

import solvis
from solvis.filter.rupture_id_filter import FilterRuptureIds
from solvis.solution.fault_system_solution import FaultSystemSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
fslt = current_model.source_logic_tree.branch_sets[0]  # PUY is used always , just for the 3 solution_ids

FSR_COLUMNS_A = 26  # see how this flies: 26
FSR_COLUMNS_B = 25  # HIK

RATE_COLUMNS_A = 6  # see how this flies:6
COMPOSITE_RATE_COLUMNS = 6


def test_from_puy_branch_solutions(puy_branch_solutions):
    print(fslt.branches)
    composite = FaultSystemSolution.from_branch_solutions(puy_branch_solutions).model
    print(composite.fault_sections_with_rupture_rates.info())
    assert composite.fault_sections_with_rupture_rates.shape == (148394, FSR_COLUMNS_A)


class TestSmallCrustal(object):
    def test_rates_shape(self, crustal_small_fss_fixture):
        rates = crustal_small_fss_fixture.model.rupture_rates
        assert rates.shape == (5, RATE_COLUMNS_A)  # no 0 rates

    def test_check_indexes(self, crustal_small_fss_fixture):
        sol = crustal_small_fss_fixture.model
        # assert sol.ruptures.index == sol.ruptures["Rupture Index"]
        assert sol.indices.index.all() == sol.indices["Rupture Index"].all()

        print(sol.composite_rates.index.names)
        assert sol.composite_rates.index.names == ['solution_id', 'Rupture Index']

        print(sol.rupture_rates.info())
        assert sol.rupture_rates["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.ruptures["Rupture Index"].dtype == pd.UInt32Dtype()
        assert sol.indices["Rupture Index"].dtype == pd.Int32Dtype()

    def test_check_types(self, crustal_small_fss_fixture):
        sol = crustal_small_fss_fixture
        assert isinstance(sol, FaultSystemSolution)
        assert sol.fault_regime == 'CRUSTAL'

        model = sol.model
        assert infer_dtype(model.rupture_rates["fault_system"]) == "string"
        assert model.rupture_rates["rate_weighted_mean"].dtype == 'float32'
        assert infer_dtype(model.indices["Num Sections"]) == "integer"
        assert model.indices["Num Sections"].dtype == "Int32"  # pd.UInt16Dtype()
        assert model.indices["# 1"].dtype == "Int32"  # pd.UInt16Dtype()

    # @pytest.mark.skip('remove deprecated')
    def test_filter_solution_ruptures(self, crustal_small_fss_fixture):
        sol = crustal_small_fss_fixture
        rupture_ids = list(FilterRuptureIds(sol.model, drop_zero_rates=True).for_rupture_rate(min_rate=1e-7))

        new_sol = solvis.FaultSystemSolution.filter_solution(sol, rupture_ids)
        assert len(rupture_ids) == new_sol.model.ruptures.shape[0]

        model = new_sol.model
        assert infer_dtype(model.rupture_rates["fault_system"]) == "string"
        assert model.rupture_rates["rate_weighted_mean"].dtype == 'float32'
        assert infer_dtype(model.indices["Num Sections"]) == "integer"
        assert model.indices["Num Sections"].dtype == "Int32"  # pd.UInt16Dtype()
        assert model.indices["# 1"].dtype == "Int32"  # pd.UInt16Dtype()


# @pytest.mark.slow
# class TestDataFrames(object):
#     def test_rates_shape(self, puysegur_fixture):
#         sol = puysegur_fixture
#         assert sol.rupture_rates.shape == (2033, RATE_COLUMNS_A)  # no 0 rates

#     def test_rates_no_missing_aggregates(self, puysegur_fixture):
#         sol = puysegur_fixture
#         print(sol.rupture_rates.info())
#         assert sol.rupture_rates["rate_weighted_mean"].count() == sol.rupture_rates.shape[0]
#         print(sol.ruptures_with_rupture_rates.info())
#         assert sol.ruptures_with_rupture_rates["rate_weighted_mean"].count() == sol.rupture_rates.shape[0]
#         assert sol.ruptures_with_rupture_rates["rate_weighted_mean"].shape[0] == sol.rupture_rates.shape[0]
#         # assert 0

#     def test_ruptures_with_rupture_rates(self, puysegur_fixture):
#         sol = puysegur_fixture
#         print(sol.ruptures_with_rupture_rates.info())
#         print()
#         print(sol.ruptures_with_rupture_rates)
#         assert sol.ruptures_with_rupture_rates.shape[0] == sol.rupture_rates.shape[0]

#     def test_rs_with_rupture_rates(self, puysegur_fixture):
#         sol = puysegur_fixture
#         print(sol.rs_with_rupture_rates.info())
#         print()
#         print(sol.rs_with_rupture_rates)
#         assert len(sol.rs_with_rupture_rates["Rupture Index"].unique()) == sol.rupture_rates.shape[0]

#     def test_fault_sections_with_rupture_rates_shape(self, puysegur_fixture):
#         sol = puysegur_fixture
#         print(sol.fault_sections_with_rupture_rates.info())
#         print()
#         print(sol.fault_sections_with_rupture_rates)
#         assert puysegur_fixture.fault_sections_with_rupture_rates.shape == (148394, FSR_COLUMNS_A)


class TestSmallDataFrames(object):
    def test_rates_shape(self, puysegur_small_fss_fixture):
        sol = puysegur_small_fss_fixture
        assert sol.model.rupture_rates.shape == (7, RATE_COLUMNS_A)  # no 0 rates

    def test_rates_no_missing_aggregates(self, puysegur_small_fss_fixture):
        model = puysegur_small_fss_fixture.model
        print(model.rupture_rates.info())
        assert model.rupture_rates["rate_weighted_mean"].count() == model.rupture_rates.shape[0]
        print(model.ruptures_with_rupture_rates.info())
        assert model.ruptures_with_rupture_rates["rate_weighted_mean"].count() == model.rupture_rates.shape[0]
        assert model.ruptures_with_rupture_rates["rate_weighted_mean"].shape[0] == model.rupture_rates.shape[0]

    def test_ruptures_with_rupture_rates(self, puysegur_small_fss_fixture):
        model = puysegur_small_fss_fixture.model
        print(model.ruptures_with_rupture_rates.info())
        print()
        print(model.ruptures_with_rupture_rates)
        assert model.ruptures_with_rupture_rates.shape[0] == model.rupture_rates.shape[0]

    def test_rs_with_rupture_rates(self, puysegur_small_fss_fixture):
        model = puysegur_small_fss_fixture.model
        print(model.rs_with_rupture_rates.info())
        print()
        print(model.rs_with_rupture_rates)
        assert len(model.rs_with_rupture_rates["Rupture Index"].unique()) == model.rupture_rates.shape[0]

    def test_fault_sections_with_rupture_rates_shape(self, puysegur_small_fss_fixture):
        model = puysegur_small_fss_fixture.model
        print(model.fault_sections_with_rupture_rates.info())
        print()
        print(model.fault_sections_with_rupture_rates)
        assert puysegur_small_fss_fixture.model.fault_sections_with_rupture_rates.shape == (83, FSR_COLUMNS_A)


class TestPuysegurSmallSurfaces(object):
    def test_rupture_surface(self, puysegur_small_fss_fixture):
        surface = puysegur_small_fss_fixture.rupture_surface(3)
        print(surface.info())
        print()
        print(surface)
        assert surface.shape == (5, FSR_COLUMNS_A)
        # assert 0

    def test_fault_surfaces(self, puysegur_small_fss_fixture):
        surfaces = puysegur_small_fss_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())
        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (271, 14)


@pytest.mark.slow
class TestHikurangi(object):
    def test_fault_sections_with_rupture_rates_shape(self, hikurangi_fixture):
        assert hikurangi_fixture.model.fault_sections_with_rupture_rates.shape == (42403, FSR_COLUMNS_B)

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
        rates = hikurangi_fixture.model.rupture_rates
        assert rates.shape == (1172, RATE_COLUMNS_A)  # no 0 rates


@pytest.mark.slow
class TestSmallHikurangi(object):
    @pytest.mark.TODO_check_values
    def test_fault_sections_with_rupture_rates_shape(self, hikurangi_small_fss_fixture):
        print(hikurangi_small_fss_fixture.model.fault_sections_with_rupture_rates)
        assert hikurangi_small_fss_fixture.model.fault_sections_with_rupture_rates.shape == (20, FSR_COLUMNS_B)

    @pytest.mark.TODO_check_values
    def test_fault_surfaces(self, hikurangi_small_fss_fixture):
        surfaces = hikurangi_small_fss_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (452, 13)

    @pytest.mark.TODO_check_values
    def test_rupture_surface(self, hikurangi_small_fss_fixture):
        surface = hikurangi_small_fss_fixture.rupture_surface(5)
        assert surface.shape == (9, FSR_COLUMNS_B)

    def test_rates_shape(self, hikurangi_small_fss_fixture):
        rates = hikurangi_small_fss_fixture.model.rupture_rates
        assert rates.shape == (3, RATE_COLUMNS_A)  # no 0 rates

    # def test_write_read_archive_filtered_incompatible(self, crustal_fixture):

    #     folder = tempfile.TemporaryDirectory()
    #     # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    #     new_path = pathlib.Path(folder.name, 'test_incompatible_filtered_archive.zip')

    #     fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
    #     ref_solution = pathlib.PurePath(fixture_folder, ARCHIVES['CRU'])

    #     rr = crustal_fixture.rupture_rates
    #     ruptures = rr[rr['rate_mean'] > 1e-6]["Rupture Index"].unique()
    #     print(ruptures)
    #     new_sol = solvis.FaultSystemSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=False)
    #     read_sol = solvis.FaultSystemSolution.from_archive(new_path)

    #     print(read_sol.rupture_rates)
    #     print(crustal_fixture.rupture_rates)
    #     # assert read_sol.rupture_rates['Rupture Index'].all() == crustal_fixture.rupture_rates['Rupture Index'].all()

    #     assert read_sol.rupture_rates.columns.all() == crustal_fixture.rupture_rates.columns.all()
    #     assert read_sol.rupture_rates.shape[1] == crustal_fixture.rupture_rates.shape[1]

    #     assert read_sol.indices.shape[0] == len(ruptures)
    #     assert read_sol.rupture_rates.shape[0] == len(ruptures)
    #     assert read_sol.ruptures.shape[0] == len(ruptures)

    # def test_write_read_archive_filtered_compatible(self, crustal_fixture):

    #     folder = tempfile.TemporaryDirectory()
    #     # folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    #     new_path = pathlib.Path(folder.name, 'test_compatible_filtered_archive.zip')

    #     fixture_folder = pathlib.PurePath(os.path.realpath(__file__)).parent / "fixtures"
    #     ref_solution = pathlib.PurePath(fixture_folder, CRU_ARCHIVE)

    #     rr = crustal_fixture.rupture_rates
    #     ruptures = rr[rr['rate_mean'] > 1e-6]["Rupture Index"].unique()
    #     print(ruptures)
    #     new_sol = solvis.FaultSystemSolution.filter_solution(crustal_fixture, ruptures)

    #     new_sol.to_archive(str(new_path), ref_solution, compat=True)
    #     read_sol = solvis.FaultSystemSolution.from_archive(new_path)

    #     print(read_sol.rupture_rates)
    #     print(crustal_fixture.rupture_rates)

    #     assert read_sol.rupture_rates.columns.all() == crustal_fixture.rupture_rates.columns.all()
    #     assert read_sol.rupture_rates.shape[1] == crustal_fixture.rupture_rates.shape[1]

    #     assert read_sol.indices.shape[0] == len(ruptures)
    #     assert read_sol.rupture_rates.shape[0] == len(ruptures)
    #     assert read_sol.ruptures.shape[0] == len(ruptures)
