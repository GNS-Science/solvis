#!python3

import os
from pathlib import PurePath

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from solvis.inversion_solution import InversionSolution

def demo1():
    sr = sol.rs_with_rates
    print("Query: Query: sections with rate (sr) where sr['rupture']==5]")
    print(sr[sr['rupture']==5])
    print()

    print("Query: sections with rate (sr) where (sr['section']==1010) & (sr['Magnitude']<7.5)")
    print(sr[(sr['section']==1010) & (sr['Magnitude']<7.5)].count())
    print()

    print("Count of sections with rate (sr) where (sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count()")
    print(sr[(sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count())
    print()

def demo2(parent_fault_name: str ='Whitemans Valley'):
    sr = sol.rs_with_rates
    print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
    acton_sects = sol.fault_sections[sol.fault_sections['ParentName']==parent_fault_name]
    qdf = gpd.GeoDataFrame(sr.join(acton_sects, 'section', how='inner'))
    return qdf
    # print(qry)
    # print("qry[(qry['Annual Rate']>=1e-9) & (qry['Magnitude']<7.5)]")
    # print(qry[(qry['Annual Rate']>=1e-9) & (qry['Magnitude']<7.5)])
    # print()
    #Geometry based query


#rupture_sections_in_area
def geom_demo1(polygon):
    sr = sol.rs_with_rates
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    q1 = q0[q0['geometry'].intersects(polygon)] #whitemans_0)]
    qdf = gpd.GeoDataFrame(sr.join(q1, 'section', how='inner'))
    return qdf


def get_ruptures_for_parent_fault(parent_fault_name: str):
    # sr = sol.rs_with_rates
    # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
    sects = sol.fault_sections[sol.fault_sections['ParentName']==parent_fault_name]
    qdf = sol.rupture_sections.join(sects, 'section', how='inner')
    return qdf.rupture.unique()

#return a series of the unique rupture ids for ruptures intersecting the polygon
def get_ruptures_intersecting(polygon):
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    q1 = q0[q0['geometry'].intersects(polygon)] #whitemans_0)]
    sr = sol.rs_with_rates
    qdf = sr.join(q1, 'section', how='inner')
    return qdf.rupture.unique()

# def sections_rates_for_ruptures(ruptures: pd.Series):
#     #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
#     sr = sol.rs_with_rates
#     return sr[sr.rupture.isin(list(ruptures))]


#filtered_rupture_sections (with gemoetry)
def section_participation(df_ruptures: pd.DataFrame):
    #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
    sr = sol.rs_with_rates
    filtered_sections_with_rates_df = sr[(sr.rupture.isin(list(df_ruptures.rupture))) & (sr['Annual Rate']>0)]
    # print("Pivot table (note precision is not lost!!)")
    # participation (sum of rate) for every rupture though a point
    section_sum_of_rates_df = filtered_sections_with_rates_df.pivot_table(values='Annual Rate', index= ['section'], aggfunc=np.sum)
    q0 = gpd.GeoDataFrame(sol.fault_sections)
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

whitemans_0 = Polygon([(174.892,-41.3), (174.9, -41.345), (174.91, -41.33), (174.922, -41.32), (174.9360, -41.298)])

nap_hast = Polygon([ (176.7563, -39.4468),
                    (177.0886,-39.4426 ),
                    (177.1078, 39.7220),
                    (176.7563, -39.7178),
                    (176.7563, -39.4468)
                    ])

wlg_hex = Polygon([ (175.5780, -40.5472),
                     (176.1053, -41.2902),
                     (175.3418, -42.0656),
                     (174.0839, -42.0411),
                     (173.4357, -41.3315),
                     (174.1223, -40.5305),
                     (175.5780, -40.5472)
                     ])


"""

Some sample data - download to your WORKPATH folder
"""

#name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTUzNm9KUmJn.zip"
# 60m
name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTc1MlBDZllC.zip"
# 60hrs
#name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip"

WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))


sol = InversionSolution(PurePath(WORK_PATH,  name))

def demo_polygon_to_mfd():
    riw = get_ruptures_intersecting(wlg_hex)
    rr = sol.ruptures_with_rates
    wmfd = mfd_hist(rr[rr["Rupture Index"].isin(list(riw))])

def demo_parent_fault_mfd():
    rr = sol.ruptures_with_rates # for all the solution
    kr = get_ruptures_for_parent_fault("Kongahau")
    kmfd = mfd_hist(rr[rr["Rupture Index"].isin(list(kr))])


if __name__ == "__main__":

    # print("Done")
    wlg1 = geom_demo1(wlg_hex)
    wlg2 = geom_demo2(wlg1[wlg1['Annual Rate']>1e-6])
    export_geojson(gpd.GeoDataFrame(wlg2), "wlg_hex_60m_rate_above_1e-6.geojson")