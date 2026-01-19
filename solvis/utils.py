"""Helper functions for solvis."""

from pathlib import Path
from typing import Union

import geopandas as gpd
import pandas as pd


def mfd_hist(ruptures_df: pd.DataFrame, rate_column: str = "Annual Rate") -> pd.Series:
    """Generate a magnitude frequency distribution (MFD) from a DataFrame of ruptures.

    Args:
        ruptures_df: dataframe of ruptures
        rate_column: the dataframe column name containing the ruputre rates

    Returns:
        a pandas Series of the MFD histogram.

    Example:
        ```py
        solution = InversionSolution.from_archive("InversionSolution.zip")
        mfd = mfd_hist(solution.model.ruptures_with_rupture_rates)
        ```
    """
    # https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    # Added observed=True in advance of default change (from False) as advised in pandas FutureWarning
    mfd = ruptures_df.groupby(pd.cut(ruptures_df.Magnitude, bins=bins), observed=True)[rate_column].sum()
    return mfd


def export_geojson(gdf: gpd.GeoDataFrame, filename: Union[str, Path], **kwargs):
    """Export GeoDataFrame to json file.

    Args:
        gdf: a GeoDataFrame to export to file
        filename: the path of the file:
        **kwargs: key-word arguments to pass to the GeoDataFrame.to_json() function.
    """
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json(**kwargs))
    f.close()
