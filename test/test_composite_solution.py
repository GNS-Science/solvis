# import nzshm_common
import os
import pathlib

import nzshm_model as nm

import solvis
from solvis.inversion_solution.composite_solution import CompositeSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

current_model = nm.get_model_version(nm.CURRENT_VERSION)
slt = current_model.source_logic_tree()

CRU_ARCHIVE = "ModularAlpineVernonInversionSolution.zip"
HIK_ARCHIVE = "AveragedHikurangiInversionSolution-QXV0b21hdGlvblRhc2s6MTA3MzMy.zip"
PUY_ARCHIVE = "PuysegurInversionSolution-QXV0b21hdGlvblRhc2s6MTExMDA1.zip"

def get_solution(id: str) -> InversionSolution:

    files = dict(
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ2=CRU_ARCHIVE,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQz=CRU_ARCHIVE,
        U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTE4NTQ1=CRU_ARCHIVE,
    )

    folder = pathlib.PurePath(os.path.realpath(__file__)).parent
    filename = pathlib.PurePath(folder, f"fixtures/{files[id]}")
    return InversionSolution().from_archive(str(filename))


# def build_rates(solutions):
#     # combine the rupture rates from all solutinos
#     all_rates_df = None
#     for sb in solutions:
#         # print(sb, sb.branch.inversion_solution_id)
#         more_df = sb.rates[sb.rates['Annual Rate'] > 0]
#         more_df.insert(0, 'solution_id', sb.branch.inversion_solution_id)
#         if not isinstance(all_rates_df, pd.DataFrame):
#             all_rates_df = pd.concat([more_df], ignore_index=True)
#         else:
#             all_rates_df = pd.concat([all_rates_df, more_df], ignore_index=True)
#     all_rates_df.solution_id = all_rates_df.solution_id.astype('category')
#     return all_rates_df


def branch_solutions(fslt):
    for branch in fslt.branches:
        yield BranchInversionSolution.new_branch_solution(get_solution(branch.inversion_solution_id), branch)


def test_from_branch_solutions():
    fslt = slt.fault_system_branches[0]  # PUY
    print(fslt.branches)
    composite = CompositeSolution.from_branch_solutions(branch_solutions(fslt))

    print(composite)
    print(composite.rupture_sections.columns)
    print(composite.rupture_sections.shape)
    print()

    print(composite.rs_with_rates.columns)
    print(composite.rs_with_rates.shape)
    print()

    print(composite.fault_sections_with_rates.columns)
    print(composite.fault_sections_with_rates.shape)
    print()
    # assert 0


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
