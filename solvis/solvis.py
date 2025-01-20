#!python3
"""
Some original solvis API helper functions are defined in this module.

But most are now deprecated and replaced by equivalent filter and model methods.
"""
from pathlib import Path
from typing import Union

import geopandas as gpd
import pandas as pd


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
