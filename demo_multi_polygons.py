from functools import partial

import os
import itertools
import random

from pathlib import PurePath
import threading
import concurrent.futures

from solvis import *


polygon_query_cache = {}
polygon_lock = threading.Lock()
combo_cache = {}
combo_lock = threading.Lock()

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



def process(sol, cities, site_keys, radius):
    rupts_in_all_locs = set(sol.ruptures['Rupture Index'])

    #global polygon_query_cache
    locations = {}
    for sk in site_keys:
        locations[sk] = cities[sk]

    # print("locations", locations)
    # assert 0

    for key, location in locations.items():
        #print(location)

        polygon = circle_polygon(radius_m=radius, lat=location[1], lon=location[2])

        #cache the query result
        rupts = polygon_query_cache.get(f'{key}:{radius}', None)
        if rupts is None:
            rupts = sol.get_ruptures_intersecting(polygon)
            with polygon_lock:
                polygon_query_cache[f'{key}:{radius}'] = rupts

        print(f"city: {key}, radius: {radius} , Pop: {location[3]}, ruptures: {len(rupts)}")
        if len(rupts) == 0:
            return new_sol(sol, rupts)

        rupts_in_all_locs = rupts_in_all_locs.intersection(set(rupts))

    return new_sol(sol, rupts_in_all_locs)


def proc_radius(site_set, radius, rate_thresholds):

    #cache the query result
    key = ".".join(site_set[:-1])
    rupts = combo_cache.get(f'{key}:{radius}', None)
    if rupts  == 0:
        print('skip cause no rupts here')
        return
    else:
        subset = process(sol[1], cities, site_set, radius)
        rates = subset.rates
        with combo_lock:
            combo_cache[f'{key}:{radius}'] = rates.shape[0]

    print(f"{rates.shape[0]} events total for {site_set} ")
    if rates.shape[0] == 0:
        return

    for threshold in rate_thresholds:
        unique_events = set()
        rated_events = rates[rates['Annual Rate']>threshold]
        if rated_events.shape[0] >0:
            print (f"{rated_events.shape[0]} events with rate > {threshold} for {site_set} ")
            idxs = list(rated_events["Rupture Index"])
            for idx in idxs:
                if not idx in unique_events:
                    # for site in site_set:
                    yield (i, sol[0], site_set, radius, idx)
        else:
            return




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
        QN = ["Greymouth", -45.03, 168.66, 15e3],
        AK = ["Auckland", -36.848461, 174.763336, 2e6],
    )

    combos = city_combinations(cities, 0)
    # combos = random.Random().choices(combos, k=10)

    print(f"city combos: {len(combos)}")

    #name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip"
    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip" #60hrs!
    #60hr
    WORK_PATH = "/home/chrisbc/DEV/GNS/opensha-modular/solvis"
    #os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))

    sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))
    solutions = [("60hr-J0YWJU.zip", sol)]
    radii = [10e3,30e3,60e3,100e3] #AK could be larger ??
    rate_thresholds = [0,1e-15,1e-12,1e-9,1e-6]
    radii.reverse()
    rate_thresholds.reverse()

    count = 0
    for (sol, site_set, radius, rate_threshold) in itertools.product(solutions, combos, radii, rate_thresholds):
        count +=1
    print(f"{count} permutations")

     #_df = pd.DataFrame(columns=['City Code', 'Site Radius', 'Rupture Index'])
    out_file = f"DATA/rupts_sol({sol[0]}).csv"
    site_rupts = []
    i, writes = 0, 0

    for sol in solutions:
        for site_set in combos:
            print(f"{site_set}")
            site_radius_rupts = []
            for radius in radii:
                for row in proc_radius(site_set, radius, rate_thresholds):
                    site_radius_rupts.append(row)
                    i+=1

            #site_set dataframe
            df = pd.DataFrame(site_radius_rupts, columns=["Index", 'Solution ID', 'City Codes', 'Site Radius', 'Rupture Index'])
            if writes == 0:
                df.to_csv(out_file)
            else:
                df.to_csv(out_file, mode='a', header=False)
            writes +=1


