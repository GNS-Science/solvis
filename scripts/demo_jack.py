import nzshm_model as nm
import json
import pathlib

from shapely.geometry import shape
from shapely.geometry.polygon import Polygon

from solvis import CompositeSolution, FaultSystemSolution, export_geojson

# load the geomtry
geojson = json.load(open('WORK/DUD/orb_area_polygon.geojson'))
polygon: Polygon = shape(geojson['features'][0]['geometry'])

# load the model
slt = nm.get_model_version("NSHM_v1.0.4").source_logic_tree()
comp = CompositeSolution.from_archive("WORK/NSHM_v1.0.4_CompositeSolution.zip", slt)

# get the crustal fault solutions
fss: FaultSystemSolution = comp._solutions['CRU']  # NB this API call will change in the future

# get the rupture_ids ...
rupture_ids: list = fss.get_ruptures_intersecting(polygon)

# Use the rupture _ids to filter the solution dataframes
# Ruptures and Rates (aggregated from underlying InversionSolutions)
rr = fss.ruptures_with_rupture_rates  # complete crustal solution df has 3884 ruptures
print(rr[rr['Rupture Index'].isin(rupture_ids)])  # 270 of these are intersecting the polygon

# Composite rates dataframe has one record per contributing InversionSolution
cr = fss.composite_rates

# Show all
print(cr[cr['Rupture Index'].isin(rupture_ids)])

# Show a given solution
print(cr[(cr['solution_id'] == 'U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy') & (cr['Rupture Index'].isin(rupture_ids))])

# more filtering examples
print("aggregate ruptures with rate >=1e-9) & magnitude<7.5)")
print(rr[(rr['rate_weighted_mean'] >= 1e-9) & (rr['Magnitude'] < 7.5)])
print()

# Other dataframes of interest ...
print(fss.fault_sections)


## now export some individual rupture geojson
def save_geojson(fss: FaultSystemSolution, rupture_id: int):
    rupture_surface_gdf = fss.rupture_surface(rupture_id).drop(
        columns=[
            'key_0',
            'fault_system',
            'Rupture Index',
            'rate_max',
            'rate_min',
            'rate_count',
            'rate_weighted_mean',
            'Magnitude',
            'Average Rake (degrees)',
            'Area (m^2)',
            'Length (m)',
        ]
    )
    rupture_surface_gdf = rupture_surface_gdf.reset_index()
    export_geojson(rupture_surface_gdf, filename=pathlib.Path("JackDemo_" + str(rupture_id) + ".geojson"))


for rid in rupture_ids[:3]:
    save_geojson(fss, rid)
