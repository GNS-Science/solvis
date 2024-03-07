#!python3

# from functools import partial
from pathlib import Path
from typing import Callable, Iterable, List, Union

import geopandas as gpd
import numpy as np
import pandas as pd

from solvis.inversion_solution.typing import InversionSolutionProtocol


def parent_fault_names(
    sol: InversionSolutionProtocol, sort: Union[None, Callable[[Iterable], List]] = sorted
) -> List[str]:
    if sort:
        return sort(sol.fault_sections.ParentName.unique())
    return list(sol.fault_sections.ParentName.unique())


# filtered_rupture_sections (with geometry)
def section_participation(sol: InversionSolutionProtocol, df_ruptures: pd.DataFrame = None):
    sr = sol.rs_with_rupture_rates
    if df_ruptures is not None:
        filtered_sections_with_rates_df = sr[(sr["Rupture Index"].isin(list(df_ruptures))) & (sr['Annual Rate'] > 0)]
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


def mfd_hist(ruptures_df: pd.DataFrame, rate_column: str = "Annual Rate"):
    # https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    mfd = ruptures_df.groupby(pd.cut(ruptures_df.Magnitude, bins=bins))[rate_column].sum()
    return mfd


def export_geojson(gdf: gpd.GeoDataFrame, filename: Union[str, Path], **kwargs):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json(**kwargs))
    f.close()


def rupt_ids_above_rate(sol: InversionSolutionProtocol, rate: float, rate_column: str = "Annual Rate"):
    rr = sol.rupture_rates
    if not rate:
        return rr["Rupture Index"].unique()
    return rr[rr[rate_column] > rate]["Rupture Index"].unique()
