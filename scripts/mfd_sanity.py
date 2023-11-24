"""Sanity check MFD values in complete composite solution."""
import os
import pathlib
import click
import time
import nzshm_model
import pandas as pd

from solvis import CompositeSolution


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|


def build_mfd(
    fault_sections_gdf: pd.DataFrame,
    rate_col: str,
    magnitude_col: str,
    min_mag: float = 6.8,
    max_mag: float = 9.5,
) -> pd.DataFrame:
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    df = pd.DataFrame({"rate": fault_sections_gdf[rate_col], "magnitude": fault_sections_gdf[magnitude_col]})

    df["bins"] = pd.cut(df["magnitude"], bins=bins)
    df["bin_center"] = df["bins"].apply(lambda x: x.mid)
    df = df.drop(columns=["magnitude"])
    df = pd.DataFrame(df.groupby(df.bin_center).sum())

    # reverse cumsum
    df['cumulative_rate'] = df.loc[::-1, 'rate'].cumsum()[::-1]
    df = df.reset_index()
    df.bin_center = pd.to_numeric(df.bin_center)
    df = df[df.bin_center.between(min_mag, max_mag)]
    return df


def all_mfds_mode_A(comp, slt, fs: str = 'CRU'):
    """build them the long-hand way"""

    def generate_fault_system_mfds(comp, fs: str = 'CRU'):

        fss = comp._solutions[fs]
        # cr = comp.composite_rates # the rates dataframe with original source solution rates
        crr = comp.composite_rates.join(fss.ruptures.drop(columns="RuptureIndex"), on="RuptureIndex")

        for fslt in slt.fault_system_lts:
            if not fslt.short_name == fs:
                continue
            else:
                for fslt_branch in fslt.branches:
                    df = crr[crr.solution_id == fslt_branch.inversion_solution_id]
                    yield (
                        fslt_branch.values,
                        fslt_branch.inversion_solution_id,
                        fslt_branch.weight,
                        build_mfd(df, "Annual Rate", "Magnitude"),
                    )

    all_mfds = pd.DataFrame(columns=["sid", "vals", "weight", "bin_center", "rate", "cumulative_rate"])
    for (vals, sid, weight, mfd) in generate_fault_system_mfds(comp, fs):
        mfd["sid"] = sid
        mfd['vals'] = str(vals)
        mfd['weight'] = weight
        all_mfds = pd.concat([all_mfds, mfd], ignore_index=True)

    return all_mfds


def all_mfds_mode_B(comp, fs: str = 'CRU'):
    """use the previously calculated aggregate rates"""
    fss = comp._solutions[fs]
    df0 = fss.ruptures_with_rates
    return build_mfd(df0, "rate_weighted_mean", "Magnitude")


def validate_measure(fs):

    t0 = time.perf_counter()
    slt = nzshm_model.get_model_version("NSHM_v1.0.4").source_logic_tree()
    comp = CompositeSolution.from_archive(pathlib.Path("WORK/NSHM_v1.0.4_CompositeSolution.zip"), slt)

    t1 = time.perf_counter()
    print("load solution took: %s" % (t1 - t0))

    cru_mfds = all_mfds_mode_A(comp, slt, fs)
    cru_mfds["rate_weighted"] = cru_mfds["weight"] * cru_mfds["rate"]
    cru_mfds["cum_rate_weighted"] = cru_mfds["weight"] * cru_mfds["cumulative_rate"]
    sum_mfd = pd.DataFrame(cru_mfds.groupby(cru_mfds.bin_center).sum())
    sum_mfd = sum_mfd.reset_index()

    # print("MODE A")
    # print("======")
    # print(sum_mfd)
    # print()
    t2 = time.perf_counter()

    cru_mfds_B = all_mfds_mode_B(comp, fs)
    t3 = time.perf_counter()

    assert cru_mfds_B['bin_center'].all() == sum_mfd['bin_center'].all()
    assert cru_mfds_B['rate'].all() == sum_mfd['rate_weighted'].all()
    assert cru_mfds_B['cumulative_rate'].all() == sum_mfd['cum_rate_weighted'].all()

    print("MODE A and MODE B produce identical MFD")
    print("MODE A calc took: %s" % (t2 - t1))
    print("MODE B (fast indices) calc took: %s" % (t3 - t2))
    print()
    print("MODE B")
    print("======")
    print(cru_mfds_B)


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|


@click.command()
@click.option('--fault_system', '-fs', default='PUY', type=click.Choice(['PUY', 'HIK', 'CRU', 'ALL']))
@click.option('--work_folder', '-w', default=lambda: os.getcwd())
def cli(work_folder, fault_system):
    """FaultSystemSolution tasks - build, analyse."""
    click.echo(f"work folder: {work_folder}")
    click.echo(f"fault system: {fault_system}")
    validate_measure(fault_system)


if __name__ == "__main__":
    cli()
