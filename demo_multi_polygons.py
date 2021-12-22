from functools import partial

import os

from pathlib import PurePath

from solvis import *


def export(sol):
    # #wlg_above_sol == new_sol(ri_sol, above)
    # sp0 = section_participation(ri_sol, ri)

    # #write out a goejson
    radius = f"{int(radius_m/1000)}km"
    # geofile = PurePath(WORK_PATH, f"{location[0]}_ruptures_radius({radius})_rate_filter({rate_threshold}).geojson")
    # print(f"write new geojson file: {geofile}")
    # export_geojson(gpd.GeoDataFrame(sp0), geofile)

    # #write the solution
    base_archive = PurePath(WORK_PATH,  name)
    new_archive = PurePath(WORK_PATH, f"{location[0]}_ruptures_radius({radius})_rate_filter({rate_threshold})_solution.zip")
    # print(f"write new solution file: {new_archive}")
    #  print(f"Filtered InversionSolution {loc[0]} within {radius} has {ri_sol.rates[ri_sol.rates['Annual Rate']>rate_threshold].size} ruptures where rate > {rate_threshold}")

    ri_sol.to_archive(str(new_archive), str(base_archive))


def process(sol, locations):
    rupts_in_all_polys = set(sol.ruptures['Rupture Index'])
    for key, location in locations.items():
        #print(location)
        polygon = circle_polygon(radius_m=location[3], lat=location[1], lon=location[2])
        rupts = sol.get_ruptures_intersecting(polygon)

        print(f"city: {key}, radius: {location[3]}, ruptures: {len(rupts)}")
        rupts_in_all_polys = rupts_in_all_polys.intersection(set(rupts))

    return new_sol(sol, rupts_in_all_polys)


if __name__ == "__main__":


    cities = dict(
        AK = ["Auckland", -36.848461, 174.763336, 3e5],
        WN = ["Wellington", -41.276825, 174.777969, 2e5],
        GN = ["Gisborne", -38.662334, 178.017654, 2e5],
        CC = ["Christchurch", -43.525650, 172.639847, 2e5],
    )

    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip"
    WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))
    sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))

    print(f"Build Filtered Inversion Solutions for source {name}.")
    print()
    print(f"with {sol.rates[sol.rates['Annual Rate']>0].shape[0]} ruptures with rate>0.")
    print()

    site_sets = [('AK', 'WN'), ("WN", "AK", "CC")]

    def get_locations(site_set, cities):
        locations = dict()
        #print(site_set)
        for key, city in cities.items():
            #print(key)
            if key in site_set:
                locations[key] = city
        return locations

    for site_set in site_sets:
        locs = get_locations(site_set, cities)
        #print(site_set)
        rates = process(sol, locs).rates
        rate_filters = [0, 1e-15, 1e-12, 1e-9, 1e-6]
        for threshold in rate_filters:
            print (f"{rates[rates['Annual Rate']>threshold].shape[0]} events with rate > {threshold} for {site_set} ")



