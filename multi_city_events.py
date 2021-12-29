from functools import partial

import os
import itertools
import random

from pathlib import PurePath
import threading
import concurrent.futures
import csv

from solvis import *


polygon_query_cache = {}
combo_cache = {}

polygon_lock = threading.Lock()
combo_lock = threading.Lock()
writer_lock = threading.Lock()

"""
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
"""


def sum_above(key_combo, cities, limit):
    for kc in key_combo:
        pop = 0
        for key in kc:
            pop += cities[key][3] #sum population
        if pop >= limit:
            yield kc


def city_combinations(cities, pop_impacted=1e6, combo_max=5):
    combos = []
    for rng in range(2, max(len(cities),combo_max)):
        combos.extend(sum_above([c for c in itertools.combinations(cities, rng)], cities, pop_impacted))
    return combos


def pre_process(sol, cities, site_keys, radii):
    rupts_in_all_locs = set(sol.ruptures['Rupture Index'])

    locations = {}
    for sk in site_keys:
        locations[sk] = dict(info=cities[sk])

    for site_key, location in locations.items():
        location['radius'] = {}
        for radius in radii:
            location['radius'][radius] = {}
            polygon = circle_polygon(radius_m=radius, lat=location['info'][1], lon=location['info'][2])
            rupts = sol.get_ruptures_intersecting(polygon)
            print(f"city: {site_key}, radius: {radius} , Pop: {location['info'][3]}, ruptures: {len(rupts)}")
            location['radius'][radius]['ruptures'] = rupts
    return locations


if __name__ == "__main__":

    cities = dict(
        WN = ["Wellington", -41.276825, 174.777969, 2e5],
        GN = ["Gisborne", -38.662334, 178.017654, 5e4],
        CC = ["Christchurch", -43.525650, 172.639847, 3e5],
        IN = ["Invercargill", -46.413056, 168.3475, 8e4],
        DN = ["Dunedin", -45.8740984, 170.5035755, 1e5],
        NP = ["Napier", -39.4902099, 176.917839, 8e4],
        NY = ["New Plymouth", -39.0579941, 174.0806474, 8e4],
        PN = ["Palmerston North", -40.356317, 175.6112388, 7e4],
        NL = ["Nelson", -41.2710849, 173.2836756, 8e4],
        BL = ["Blenheim", -41.5118691, 173.9545856, 5e4],
        WK = ["Whakatane", -37.9519223, 176.9945977, 5e4],
        GR = ["Greymouth", -42.4499469, 171.2079875, 3e4],
        QN = ["Queenstown", -45.03, 168.66, 15e3],
        AK = ["Auckland", -36.848461, 174.763336, 2e6],
    )

    combos = city_combinations(cities, 0)
    #combos.reverse()
    # combos = random.Random().choices(combos, k=10)

    print(f"city combos: {len(combos)}")
    print(combos)

    #name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip"
    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip" #60hrs!
    #60hr
    WORK_PATH = "/home/chrisbc/DEV/GNS/opensha-modular/solvis"
    #os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))

    sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))
    solutions = [("60hr-J0YWJU.zip", sol)]
    radii = [100e3, 60e3, ]#30e3,60e3,100e3] #AK could be larger ??
    rate_thresholds = [0,1e-15,1e-12,1e-9,1e-6]
    radii.reverse()
    rate_thresholds.reverse()


    city_radius_ruptures = pre_process(sol, cities, cities.keys(), radii)
    #print(city_radius_ruptures)

    rupture_radius_site_sets = {}
    site_set_rupts = {}

    for site_set in combos:
        for radius in radii:
            events = set(sol.ruptures['Rupture Index'])
            if len(events) == 0:
                continue
            for site in site_set:
                events = set(city_radius_ruptures[site]['radius'][radius]['ruptures']).intersection(events)

            if len(events):
                ra = sol.rates
                rates = ra[ra["Rupture Index"].isin(list(events))]
                hits = rates[rates['Annual Rate'] >0]
                print(site_set, radius, len(events), hits.shape[0])
                if hits.shape[0] > 0:
                    for row in hits.itertuples():
                        rupture_idx = row[0]
                        current = rupture_radius_site_sets.get(rupture_idx, {}).get(radius)
                        if not current:
                            pass
                        elif len(current) < len(site_set):
                            print("update ", rupture_idx, radius, "from", current, "to", site_set)
                        else:
                            continue
                        if not rupture_radius_site_sets.get(rupture_idx):
                            rupture_radius_site_sets[rupture_idx] = {}
                        rupture_radius_site_sets[rupture_idx][radius] = site_set

            else:
                print(site_set, radius, None)

    print(rupture_radius_site_sets[426336])
    print("Done")