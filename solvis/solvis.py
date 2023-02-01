#!python3

# from functools import partial
from pathlib import Path
from typing import Union

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, Polygon

from solvis.inversion_solution import InversionSolution

# def sections_rates_for_ruptures(ruptures: pd.Series):
#     #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
#     sr = sol.rs_with_rates
#     return sr[sr.rupture.isin(list(ruptures))]


# filtered_rupture_sections (with gemoetry)
def section_participation(sol: InversionSolution, df_ruptures: pd.DataFrame = None):
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


def export_geojson(gdf: gpd.GeoDataFrame, filename: Union[str, Path]):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json())
    f.close()


def new_sol(sol: InversionSolution, rupture_ids: npt.ArrayLike) -> InversionSolution:
    rr = sol.ruptures
    ra = sol.rates
    ri = sol.indices
    ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
    rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
    indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

    # all other props are derived from these ones
    ns = InversionSolution()
    ns.set_props(rates, ruptures, indices, sol.fault_sections.copy())
    return ns


def rupt_ids_above_rate(sol: InversionSolution, rate: float):
    rr = sol.rates
    if not rate:
        return rr["Rupture Index"].unique()
    return rr[rr['Annual Rate'] > rate]["Rupture Index"].unique()


def circle_polygon(radius_m: int, lat: float, lon: float):
    # based on https://gis.stackexchange.com/a/359748
    # updated with https://pyproj4.github.io/pyproj/stable/gotchas.html#upgrading-to-pyproj-2-from-pyproj-1

    local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(lat, lon)
    wgs84_projection = "+proj=longlat +datum=WGS84 +no_defs"

    transformer = Transformer.from_crs(wgs84_projection, local_azimuthal_projection)
    point_transformed = transformer.transform(lon, lat)

    buffer = Point(point_transformed).buffer(radius_m)

    # Get polygon with lat lon coordinates
    transformer2 = Transformer.from_crs(local_azimuthal_projection, wgs84_projection)
    lons, lats = transformer2.transform(*buffer.exterior.xy)

    # Add 360 to all negative longitudes
    points = []
    for i in range(len(lons)):
        lon = lons[i]
        if lon < 0:
            lon += 360
        points.append(Point(lon, lats[i]))

    return Polygon(points)
