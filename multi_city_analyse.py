
import pandas as pd
import geopandas as gpd
from solvis import *

CITY_CODE_LENGTH = 3

def where_n_cities_are_within_d_km(df, n, d):
    return df[f'r{int(d)}km'].apply(lambda x: len(x) if x else 0) > (CITY_CODE_LENGTH*n)


def where_city_within_d_km(df: pd.DataFrame, city: str, d: int):
    return df[f'r{int(d)}km'].apply(lambda x: city in x if x else False) == True


name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip" #60hrs!
WORK_PATH = "/home/chrisbc/DEV/GNS/opensha-modular/solvis"
sol = InversionSolution().from_archive(PurePath(WORK_PATH,  name))

df = pd.read_json('multi_city_ruptures_60hr.json')

# print(df[
#     where_city_within_d_km(df, 'WN', 30) &\
#     where_n_cities_are_within_d_km(df, 3, 30) &\
#     (df['Annual Rate'] >=1e-6)])


idxs = list(df[
    where_city_within_d_km(df, 'HLZ', 50) &\
    (df['Annual Rate'] >=1e-6)]['Rupture Index'])
    # where_n_cities_are_within_d_km(df, 3, 50) &\

print( len(idxs) )

result = new_sol(sol, idxs)

sp0 = section_participation(result, idxs)
export_geojson(gpd.GeoDataFrame(sp0), 'geofile.geojson')

