#!python3

# from functools import partial
from pathlib import Path
from typing import Union

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import pandas as pd

from solvis.inversion_solution import CompositeSolution, InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

# def sections_rates_for_ruptures(ruptures: pd.Series):
#     #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
#     sr = sol.rs_with_rates
#     return sr[sr.rupture.isin(list(ruptures))]


# filtered_rupture_sections (with gemoetry)
def section_participation(sol: InversionSolutionProtocol, df_ruptures: pd.DataFrame = None):
    sr = sol.rs_with_rates
    if df_ruptures is not None:
        filtered_sections_with_rates_df = sr[(sr.rupture.isin(list(df_ruptures))) & (sr['Annual Rate'] > 0)]
    else:
        filtered_sections_with_rates_df = sr

    # print("Pivot table (note precision is not lost!!)")
    # participation (sum of rate) for every rupture though a point
    section_sum_of_rates_df = filtered_sections_with_rates_df.pivot_table(
        values='Annual Rate', index=['section'], aggfunc=np.sum
    )
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    # print (q0)
    # print(section_sum_of_rates_df)
    return section_sum_of_rates_df.join(q0, 'section', how='inner')


def mfd_hist(ruptures_df: pd.DataFrame):
    # https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    mfd = ruptures_df.groupby(pd.cut(ruptures_df.Magnitude, bins=bins)).sum()['Annual Rate']
    return mfd


def export_geojson(gdf: gpd.GeoDataFrame, filename: Union[str, Path], **kwargs):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json(**kwargs))
    f.close()


def filter_solution(
    sol: InversionSolutionProtocol, rupture_ids: npt.ArrayLike
) -> Union[InversionSolution, CompositeSolution]:
    klass = type(sol)
    return klass.filter_solution(sol, rupture_ids)


def rupt_ids_above_rate(sol: InversionSolutionProtocol, rate: float):
    rr = sol.rates
    if not rate:
        return rr["Rupture Index"].unique()
    return rr[rr['Annual Rate'] > rate]["Rupture Index"].unique()
