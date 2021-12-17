#! python demo.py

import os
from pathlib import PurePath
from shapely.geometry import Polygon
from solvis import *

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
    return gpd.GeoDataFrame(sr.join(acton_sects, 'section', how='inner'))

#rupture_sections_in_area
def geom_demo1(polygon):
    sr = sol.rs_with_rates
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    q1 = q0[q0['geometry'].intersects(polygon)] #whitemans_0_polygon)]
    qdf = gpd.GeoDataFrame(sr.join(q1, 'section', how='inner'))
    return qdf


whitemans_0_polygon = Polygon([(174.892,-41.3), (174.9, -41.345), (174.91, -41.33), (174.922, -41.32), (174.9360, -41.298)])

nap_hast_polygon = Polygon([ (176.7563, -39.4468),
                    (177.0886,-39.4426 ),
                    (177.1078, 39.7220),
                    (176.7563, -39.7178),
                    (176.7563, -39.4468)
                    ])

wlg_hex_polygon = Polygon([ (175.5780, -40.5472),
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
name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTUzNm9KUmJn.zip"
# 60m
name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTc1MlBDZllC.zip"
# 60hrs
#name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip"

WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))

sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))

def demo_polygon_to_mfd():
    riw = sol.get_ruptures_intersecting(wlg_hex_polygon)
    rr = sol.ruptures_with_rates
    return mfd_hist(rr[rr["Rupture Index"].isin(list(riw))])

def demo_parent_fault_mfd():
    rr = sol.ruptures_with_rates # for all the solution
    kr = sol.get_ruptures_for_parent_fault("Kongahau")
    return mfd_hist(rr[rr["Rupture Index"].isin(list(kr))])


def demo_polygon_to_geojson(polygon=None, rate_threshold=1e-8):
    riw = sol.get_ruptures_intersecting(polygon)
    #rs = sol.rs_with_rates
    wsp0 = section_participation(sol, riw)
    #wmfd0 = mfd_hist(rs[rs["Rupture Index"].isin(list(riw))])
    wsp1 = wsp0[wsp0['Annual Rate']>rate_threshold]

    export_geojson(gpd.GeoDataFrame(wsp0), "wlg_hex_polygon_60m.geojson")
    export_geojson(gpd.GeoDataFrame(wsp1), f"wlg_hex_polygon_60m_rate_above_{rate_threshold}.geojson")


def demo_mfd_comparison(rate_threshold=1e-8):

    print(f"compare raw, with rate_above_{rate_threshold}")
    print("========================================")

    rr = sol.ruptures_with_rates
    mfd0 = mfd_hist(rr)
    mfd1 = mfd_hist(rr[rr['Annual Rate']>rate_threshold])
    print(mfd0.compare(mfd1))


def demo_all_nz_to_geojson(rate_threshold=1e-8):
    ##BROKEN (BRAin fade)
    sr = sol.rs_with_rates
    #sr[(sr.rupture.isin(list(df_ruptures))) & (sr['Annual Rate']>0)]
    sp0 = sr.join(sol.fault_sections, 'section', how='inner')

    print(sp0)
    print(sp0.columns)
    sp1 = sp0[sp0['Annual Rate']>rate_threshold]
    export_geojson(gpd.GeoDataFrame(sp0), "all_nz_60m.geojson")
    export_geojson(gpd.GeoDataFrame(sp1), f"all_nz_60m_rate_above_{rate_threshold}.geojson")


def demo_clone_filter(polygon, rate_threshold):
    riw = sol.get_ruptures_intersecting(polygon)
    wlg_sol = new_sol(sol, riw)

    above = rupt_ids_above_rate(wlg_sol, 1e-7)
    #wlg_above_sol == new_sol(wlg_sol, above)
    wsp0 = section_participation(wlg_sol, above)

    export_geojson(gpd.GeoDataFrame(wsp0), f"region_in_poly_above-{rate_threshold}.geojson")

    #write the solution
    print("write the wlg data as a new solution file: demo_solution.zip")
    base_archive = PurePath(WORK_PATH,  name)
    wlg_sol.to_archive("demo_solution.zip", str(base_archive))


if __name__ == "__main__":

    # print(f"Demo 5")
    # print("=========")
    # demo_all_nz_to_geojson(rate_threshold=1e-8)
    # print()

    # # print("Done")
    print(f"Demo 0")
    print("=========")
    demo_polygon_to_geojson(wlg_hex_polygon)
    print()

    print(f"Demo 1")
    print("=========")
    demo1()
    print()

    print(f"Demo 2")
    print("=========")
    demo2()
    print()

    print(f"Demo 3")
    print("=========")
    demo_polygon_to_mfd()
    print()

    print(f"Demo 4")
    print("=========")
    demo_parent_fault_mfd()
    print()

    print(f"Demo 5")
    print("=========")
    demo_mfd_comparison()
    print()

    print(f"Demo 6")
    print("=========")
    demo_clone_filter(wlg_hex_polygon, 1e-6)
    print()
    print("Done")