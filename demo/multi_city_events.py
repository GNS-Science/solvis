# from functools import partial

# import os
import itertools

# import random

from pathlib import PurePath
import threading
import concurrent.futures
import csv
from datetime import datetime as dt

import pandas as pd

from solvis import *

lock = threading.Lock()


def sum_above(key_combo, cities, limit):
    for kc in key_combo:
        pop = 0
        for key in kc:
            pop += cities[key][3]  # sum population
        if pop >= limit:
            yield kc


def city_combinations(cities, pop_impacted=1e6, combo_max=5):
    combos = []
    for rng in range(1, min(len(cities), combo_max)):
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
            # print(f"city: {site_key}, radius: {radius} , Pop: {location['info'][3]}, ruptures: {len(rupts)}")
            location['radius'][radius]['ruptures'] = rupts
    return locations


def process(args):
    sol, city_radius_ruptures, rupture_radius_site_sets, site_set, radius = args[:]
    events = set(sol.ruptures['Rupture Index'])
    if len(events) == 0:
        return

    for site in site_set:
        events = set(city_radius_ruptures[site]['radius'][radius]['ruptures']).intersection(events)

    if len(events):
        for rupture_idx in events:
            current = rupture_radius_site_sets.get(rupture_idx, {}).get(radius)
            if not current:
                pass
            elif len(current) < len(site_set):
                pass
                # print("update ", rupture_idx, radius, "from", current, "to", site_set)
            else:
                continue
            with lock:
                if not rupture_radius_site_sets.get(rupture_idx):
                    rupture_radius_site_sets[rupture_idx] = {}
                rupture_radius_site_sets[rupture_idx][radius] = "_".join(site_set)


def main(sol, cities, combos, radii):
    """ """
    t0 = dt.now()
    sol = new_sol(sol, rupt_ids_above_rate(sol, 0))
    # solutions = [("60hr-J0YWJU.zip", sol)]
    t1 = dt.now()

    city_radius_ruptures = pre_process(sol, cities, cities.keys(), radii)
    t2 = dt.now()

    print(f'pre-process events for {len(cities)} cities in {(t2-t1)}')

    rupture_radius_site_sets = {}
    site_set_rupts = {}

    def generate_args(sol, city_radius_ruptures, rupture_radius_site_sets):
        for site_set in combos:
            for radius in radii:
                yield (sol, city_radius_ruptures, rupture_radius_site_sets, site_set, radius)

    t3 = dt.now()
    with concurrent.futures.ThreadPoolExecutor(4) as executor:
        for res in executor.map(process, generate_args(sol, city_radius_ruptures, rupture_radius_site_sets)):
            pass

    t4 = dt.now()
    print(f'built city events by radius in {(t4-t3)}')

    return rupture_radius_site_sets


if __name__ == "__main__":

    # ref https://service.unece.org/trade/locode/nz.htm
    cities = dict(
        WLG=["Wellington", -41.276825, 174.777969, 2e5],
        GIS=["Gisborne", -38.662334, 178.017654, 5e4],
        CHC=["Christchurch", -43.525650, 172.639847, 3e5],
        IVC=["Invercargill", -46.413056, 168.3475, 8e4],
        DUD=["Dunedin", -45.8740984, 170.5035755, 1e5],
        NPE=["Napier", -39.4902099, 176.917839, 8e4],
        NPL=["New Plymouth", -39.0579941, 174.0806474, 8e4],
        PMR=["Palmerston North", -40.356317, 175.6112388, 7e4],
        NSN=["Nelson", -41.2710849, 173.2836756, 8e4],
        BHE=["Blenheim", -41.5118691, 173.9545856, 5e4],
        WHK=["Whakatane", -37.9519223, 176.9945977, 5e4],
        GMN=["Greymouth", -42.4499469, 171.2079875, 3e4],
        ZQN=["Queenstown", -45.03, 168.66, 15e3],
        AKL=["Auckland", -36.848461, 174.763336, 2e6],
        ROT=["Rotorua", -38.1446, 176.2378, 77e3],
        TUO=["Taupo", -38.6843, 176.0704, 26e3],
        WRE=["Whangarei", -35.7275, 174.3166, 55e3],
        LVN=["Levin", -40.6218, 175.2866, 19e3],
        TMZ=["Tauranga", -37.6870, 176.1654, 130e3],
        TIU=['Timaru', -44.3904, 171.2373, 28e3],
        OAM=["Oamaru", -45.0966, 170.9714, 14e3],
        PUK=["Pukekohe", -37.2004, 174.9010, 27e3],
        HLZ=["Hamilton", -37.7826, 175.2528, 165e3],
        LYJ=["Lower Hutt", -41.2127, 174.8997, 112e3],
    )

    combos = city_combinations(cities, 0, 5)
    print(f"city combos: {len(combos)}")

    # name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTg4OG1nWFRY.zip"
    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip"  # 60hrs!

    # 60hr
    WORK_PATH = "/home/chrisbc/DEV/GNS/opensha-modular/solvis"
    # os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))

    sol = InversionSolution().from_archive(PurePath(WORK_PATH, name))

    radii = [10e3, 20e3, 30e3, 40e3, 50e3, 100e3]  # AK could be larger ??

    rupture_radius_site_sets = main(sol, cities, combos, radii)

    # now export for some science analysis
    df = pd.DataFrame.from_dict(rupture_radius_site_sets, orient='index')
    df = df.rename(columns=dict(zip(radii, [f'r{int(r/1000)}km' for r in radii])))

    print(df)
    ruptures = df.join(sol.ruptures_with_rupture_rates)

    print(ruptures)
    fname = 'multi_city_ruptures_60hr'
    ruptures.to_json(open(f'{fname}.json', 'w'), indent=2)
    ruptures.to_csv(open(f'{fname}.csv', 'w'), index=False)

    print("Done")

    try:
        print(df[df.r100km].apply(lambda x: len(x) if not x is None else 0) > (2 * 3))
    except:
        pass
