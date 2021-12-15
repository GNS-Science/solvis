#!python3

import os
from pathlib import PurePath

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from inversion_solution import InversionSolution

# def sections_rates_for_ruptures(ruptures: pd.Series):
#     #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
#     sr = sol.rs_with_rates
#     return sr[sr.rupture.isin(list(ruptures))]


#filtered_rupture_sections (with gemoetry)
def section_participation(sol: InversionSolution, df_ruptures: pd.DataFrame):
    sr = sol.rs_with_rates
    filtered_sections_with_rates_df = sr[(sr.rupture.isin(list(df_ruptures))) & (sr['Annual Rate']>0)]
    # print("Pivot table (note precision is not lost!!)")
    # participation (sum of rate) for every rupture though a point
    section_sum_of_rates_df = filtered_sections_with_rates_df.pivot_table(values='Annual Rate', index= ['section'], aggfunc=np.sum)
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    print (q0)
    print(section_sum_of_rates_df)
    df6 = section_sum_of_rates_df.join(q0, 'section', how='inner')
    return df6


def mfd_hist(ruptures_df: pd.DataFrame):
    #https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x/100, 2) for x in range(500, 910, 10)]
    mfd = ruptures_df.groupby(pd.cut(ruptures_df.Magnitude, bins=bins)).sum()['Annual Rate']
    vals = np.asarray(mfd)
    for i in range(mfd.index.size):
        print(round(mfd.index[i].mid, 2), vals[i])
    return mfd


def export_geojson(gdf: gpd.GeoDataFrame, filename):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json())
    f.close()

