#!python3
"""
The original solvis API helper functions are defined in this module.

NB please be aware that most functions in this module are deprecated and replaced
in the 2nd generation Solvis API.
"""
# from functools import partial
import warnings
from pathlib import Path
from typing import Callable, Iterable, List, Union

import geopandas as gpd
import pandas as pd

from solvis.inversion_solution.typing import InversionSolutionProtocol


def parent_fault_names(
    solution: InversionSolutionProtocol, sort: Union[None, Callable[[Iterable], List]] = sorted
) -> List[str]:
    warnings.warn("Please use InversionSolutionProtocol.parent_fault_names property instead", DeprecationWarning)
    if sort:
        return sort(solution.parent_fault_names)
    return solution.parent_fault_names


# filtered_rupture_sections (with geometry)
def section_participation(sol: InversionSolutionProtocol, df_ruptures: pd.DataFrame = None):
    warnings.warn("Please use InversionSolutionProtocol participation methods instead.", DeprecationWarning)
    rupture_ids = df_ruptures['Rupture Index'].tolist() if df_ruptures else None
    return sol.section_participation_rates(rupture_ids=rupture_ids)


def mfd_hist(ruptures_df: pd.DataFrame, rate_column: str = "Annual Rate"):
    # https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    # Added observed=True in advance of default change (from False) as advised in pandas FutureWarning
    mfd = ruptures_df.groupby(pd.cut(ruptures_df.Magnitude, bins=bins), observed=True)[rate_column].sum()
    return mfd


def export_geojson(gdf: gpd.GeoDataFrame, filename: Union[str, Path], **kwargs):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json(**kwargs))
    f.close()


def rupt_ids_above_rate(sol: InversionSolutionProtocol, rate: float, rate_column: str = "Annual Rate"):
    warnings.warn("Please use solvis.filter.FilterRuptureIds.for_rupture_rate()", DeprecationWarning)
    rr = sol.rupture_rates
    if not rate:
        return rr["Rupture Index"].unique()
    return rr[rr[rate_column] > rate]["Rupture Index"].unique()
