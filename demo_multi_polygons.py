from functools import partial

import os
import itertools
import random

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

polygon_query_cache = {}

def process(sol, cities, site_keys, radius):
    rupts_in_all_locs = set(sol.ruptures['Rupture Index'])

    #global polygon_query_cache
    locations = {}
    for sk in site_keys:
        locations[sk] = cities[sk]

    for key, location in locations.items():
        #print(location)

        # if key =="AK":
        #     polygon = circle_polygon(radius_m=radius*2, lat=location[1], lon=location[2])
        # else:
        polygon = circle_polygon(radius_m=radius, lat=location[1], lon=location[2])

        #cache the query result
        rupts = polygon_query_cache.get(f'{key}:{radius}', None)
        if rupts is None:
            rupts = sol.get_ruptures_intersecting(polygon)
            polygon_query_cache[f'{key}:{radius}'] = rupts

        print(f"city: {key}, radius: {radius} , Pop: {location[3]}, ruptures: {len(rupts)}")
        if len(rupts) == 0:
            return new_sol(sol, rupts)

        rupts_in_all_locs = rupts_in_all_locs.intersection(set(rupts))

    return new_sol(sol, rupts_in_all_locs)

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

    # count = 0
    # for (sol, site_set, radius, rate_threshold) in itertools.product(solutions, combos, radii, rate_thresholds):
    #     count +=1
    # print(f"{count} permutations")

     #_df = pd.DataFrame(columns=['City Code', 'Site Radius', 'Rupture Index'])

    site_rupts = []
    i = 0
    for sol in solutions:
        for site_set in combos:
            print(f"{site_set}")
            site_radius_rupts = []
            for radius in radii:
                subset = process(sol[1], cities, site_set, radius)
                rates = subset.rates

                print(f"{rates.shape[0]} events total for {site_set} ")
                if rates.shape[0] == 0:
                    continue

                unique_events = set()
                for threshold in rate_thresholds:
                    rated_events = rates[rates['Annual Rate']>threshold]
                    if rated_events.shape[0] >0:
                        print (f"{rated_events.shape[0]} events with rate > {threshold} for {site_set} ")
                        idxs = list(rated_events["Rupture Index"])
                        for idx in idxs:
                            if not idx in unique_events:
                                # for site in site_set:
                                row = (i, sol[0], site_set, radius, idx)
                                site_radius_rupts.append(row)
                                #print("STORE", i, sol[0], site, radius, idx)
                                i+=1
                                unique_events.add(idx)
                    else:
                        continue

            #site_set dataframe
            df = pd.DataFrame(site_radius_rupts, columns=["Index", 'Solution ID', 'City Codes', 'Site Radius', 'Rupture Index'])
            df.to_csv(f"DATA/site_rupts_sol({sol[0]})_{'-'.join(site_set)}.csv")
            site_rupts.extend(site_radius_rupts)

        #sol dataframe
        df = pd.DataFrame(site_rupts, columns=["Index", 'Solution ID', 'City Codes', 'Site Radius', 'Rupture Index'])
        df.to_csv(f"DATA/rupts_sol({sol[0]}).csv")


    """
    print(f"Build Filtered Inversion Solutions for source {name}.")
    print()
    print(f"with {sol.rates[sol.rates['Annual Rate']>0].shape[0]} ruptures with rate>0.")
    print()

    # site_sets = [('AK', 'WN'), ("WN", "AK", "CC")]

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

    """
