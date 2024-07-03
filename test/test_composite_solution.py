# import os
import pathlib
import tempfile
from copy import deepcopy
from test.conftest import branch_solutions

import geopandas as gpd
import nzshm_model as nm
import pytest

# import solvis
from solvis import CompositeSolution, FaultSystemSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree
fslt = slt.fault_system_lts[0]  # PUY is used always , just for the 3 solution_ids


FSR_COLUMNS_A = 26
FSR_COLUMNS_B = 25  # HIK
RATE_COLUMNS_A = 6


@pytest.mark.slow
class TestThreeFaultSystems(object):

    # @pytest.mark.skip('TODO_check_values')
    def test_composite_rates_shape(self, composite_fixture):
        assert composite_fixture.rupture_rates.shape == (
            4211,
            RATE_COLUMNS_A,
        )  # 3101 + 15800 + 23675 was before removing 0 rated
        assert composite_fixture.composite_rates.shape == (3 * 4211, RATE_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_rupture_surface(self, composite_fixture):
        surface = composite_fixture.rupture_surface('PUY', 3)
        print(surface)
        assert surface.shape == (5, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_sections_with_rupture_rates_shape(self, composite_fixture):
        assert composite_fixture.fault_sections_with_rupture_rates.shape == (229102, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_surfaces(self, composite_fixture):
        surfaces = composite_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (809, 15)


class TestThreeSmallFaultSystems(object):

    # @pytest.mark.skip('TODO_check_values')
    def test_composite_rates_shape(self, small_composite_fixture):
        assert small_composite_fixture.rupture_rates.shape == (
            7 + 3 + 5,  # PUY, HIK, CRU
            RATE_COLUMNS_A,
        )  # 3101 + 15800 + 23675 was before removing 0 rated
        assert small_composite_fixture.composite_rates.shape == (3 * (7 + 3 + 5), RATE_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_rupture_surface(self, small_composite_fixture):
        surface = small_composite_fixture.rupture_surface('PUY', 3)
        print(surface)
        assert surface.shape == (5, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_sections_with_rupture_rates_shape(self, small_composite_fixture):
        assert small_composite_fixture.fault_sections_with_rupture_rates.shape == (148, FSR_COLUMNS_A)

    @pytest.mark.TODO_check_values
    def test_fault_surfaces(self, small_composite_fixture):
        surfaces = small_composite_fixture.fault_surfaces()
        print(surfaces.info())
        print()
        print(surfaces.tail())

        assert isinstance(surfaces, gpd.GeoDataFrame)
        assert surfaces.shape == (809, 15)


def test_composite_serialisation(small_archives):
    folder = tempfile.TemporaryDirectory()
    # folder = pathlib.Path(pathlib.PurePath(os.path.realpath(__file__)).parent.parent, "SCRATCH")

    v1_0_0 = nm.get_model_version('NSHM_v1.0.0')
    slt = v1_0_0.source_logic_tree
    print(slt.fault_system_lts[0])

    # fudge the model branches because we have too few fixtures
    for idx in [1, 2]:
        slt.fault_system_lts[idx].branches = deepcopy(slt.fault_system_lts[0].branches)

    composite = CompositeSolution(slt)  # create the new composite solution
    for fault_system_lt in slt.fault_system_lts:
        if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
            solutions = list(
                branch_solutions(
                    fault_system_lt,
                    archive=small_archives[fault_system_lt.short_name],
                    rupt_set_id=f'rupset_{fault_system_lt.short_name}',
                )
            )

            print(solutions)
            fss = FaultSystemSolution.from_branch_solutions(solutions)

            composite.add_fault_system_solution(fault_system_lt.short_name, fss)

            # # # write the fss-archive file
            ref_solution = solutions[0].archive_path  # the file path to the reference solution
            new_path = pathlib.Path(folder.name, f'test_fault_system_{fault_system_lt.short_name}_archive.zip')

            fss.to_archive(str(new_path), ref_solution, compat=False)
            assert new_path.exists()
            assert str(fss.archive_path) == str(new_path)

    new_path = pathlib.Path(folder.name, 'test_composite_archive.zip')
    composite.to_archive(new_path)
    assert new_path.exists()
    assert str(composite.archive_path) == str(new_path)

    # remove the composite inputs ...
    for key, sol in composite._solutions.items():
        arc = pathlib.Path(sol.archive_path)
        assert arc.exists()
        arc.unlink()

    # rehydrate the composite
    new_composite = CompositeSolution.from_archive(new_path, slt)
    assert new_composite.rupture_rates.columns.all() == composite.rupture_rates.columns.all()
    assert new_composite.rupture_rates.shape == composite.rupture_rates.shape
    assert new_composite.rupture_rates['Rupture Index'].all() == composite.rupture_rates['Rupture Index'].all()


# class TestThreeFaultSystems(object):

#     @pytest.mark.skip('REVIEW')
#     def test_composite_rates_shape(self, three_branch_solutions):
#         solutions = []

#         v1_0_0 = nm.get_model_version('NSHM_1.0.0')
#         slt = v1_0_0.source_logic_tree()
#         print(slt.fault_system_lts[0])

#         # for idx in [1, 2]:
#         #     slt.fault_system_lts[idx].branches = deepcopy(slt.fault_system_lts[0].branches)

#         # for fault_system_lt in slt.fault_system_lts:
#         #     if fault_system_lt.short_name in ['CRU', 'PUY', 'HIK']:
#         #         print('extending', fault_system_lt.short_name)
#         #         solutions.extend(
#         #             puy_branch_solutions(
#         #                 fault_system_lt,
#         #                 archive=ARCHIVES[fault_system_lt.short_name],
#         #                 rupt_set_id=f'rupset_{fault_system_lt.short_name}',
#         #             )
#         #         )

#         solutions = three_branch_solutions

#         # print('solutions', len(solutions))
#         # print(solutions)
#         # print()

#         composite = FaultSystemSolution.from_branch_solutions(solutions)
#         # print( composite.aggregate_rates.info() )
#         # print( composite.aggregate_rates.head() )
#         # print( composite.aggregate_rates.tail() )

#         # assert composite.rupture_rates.shape == (3101 + 15800 + 23675, RATE_COLUMNS_A)
#         assert composite.rupture_rates.shape == (4211, RATE_COLUMNS_A)
#         assert composite.composite_rates.shape == (3 * 4211, COMPOSITE_RATE_COLUMNS)
#         # assert composite.composite_rates.shape == (127728, COMPOSITE_RATE_COLUMNS)
