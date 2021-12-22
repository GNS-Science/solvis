from functools import partial

import os

from pathlib import PurePath

from solvis import *

def process(sol, location, radius_m, rate_threshold=None):

    polygon = circle_polygon(radius_m, location[1], location[2])

    ri = sol.get_ruptures_intersecting(polygon)
    ri_sol = new_sol(sol, ri)

    # if rate_threshold>0:
    #     ri= rupt_ids_above_rate(ri_sol, rate_threshold)
    #     ri_sol = new_sol(ri_sol, ri)

    # #wlg_above_sol == new_sol(ri_sol, above)
    # sp0 = section_participation(ri_sol, ri)

    # #write out a goejson
    radius = f"{int(radius_m/1000)}km"
    # geofile = PurePath(WORK_PATH, f"{location[0]}_ruptures_radius({radius})_rate_filter({rate_threshold}).geojson")
    # print(f"write new geojson file: {geofile}")
    # export_geojson(gpd.GeoDataFrame(sp0), geofile)

    # #write the solution
    base_archive = PurePath(WORK_PATH,  name)

    for compat in [True, False]:
        new_archive = PurePath(WORK_PATH, f"{location[0]}_ruptures_radius({radius})_rate_filter({rate_threshold})_{compat}_solution.zip")
        print(f"write new solution file: {new_archive}")
        print(f"Filtered InversionSolution {loc[0]} within {radius} has {ri_sol.rates[ri_sol.rates['Annual Rate']>rate_threshold].size} ruptures where rate > {rate_threshold}")

        ri_sol.to_archive(str(new_archive), str(base_archive), compat)


if __name__ == "__main__":


    locations = dict(
        AK = ["Auckland", -36.848461, 174.763336],
        # WN = ["Wellington", -41.276825, 174.777969], #-41.288889, 174.777222], OAkley
        # GN = ["Gisborne", -38.662334, 178.017654],
        CC = ["Christchurch", -43.525650, 172.639847],
    )

    rate_filters = [1e-15, 1e-12, 1e-9, 1e-6, 0]
    rate_filters = [0, 1e-9 ]
    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTc1MlBDZllC.zip"
    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip"
    WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))
    sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))

    print(f"Build Filtered Inversion Solutions for source {name}.")
    print()
    print(f"with {sol.ruptures_with_rates[sol.ruptures_with_rates['Annual Rate']>0].size} ruptures with rate>0.")
    print()

    for threshold in rate_filters:
        for key, loc in locations.items():
            print(key, loc)
            radii = [2e4,]# 3e5, 4e5] #km
            for radius_m in radii:
                print ('process', sol, loc, radius_m, threshold)
                process(sol, loc, radius_m, threshold)



