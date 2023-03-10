
from nzshm_common.location.location import location_by_id
from solvis import geometry, CompositeSolution, export_geojson
from pathlib import Path
import nzshm_model as nm

slt = nm.get_model_version(nm.CURRENT_VERSION).source_logic_tree()

comp = CompositeSolution.from_archive(Path("WORK/CompositeSolution.zip"), slt)

POR = dict(lat=-40.30, lon=176.61)
hik = comp._solutions['HIK']
mag_775 = hik.ruptures[hik.ruptures['Magnitude'] < 7.75]['Rupture Index'].unique()

poly15 = geometry.circle_polygon(radius_m=15_000, lon=POR['lon'], lat=POR['lat'])
por15 = hik.get_ruptures_intersecting(poly15)
combo = list(set(por15).intersection(set(mag_775)))



"""
>>>hik.ruptures_with_rates[hik.ruptures_with_rates['Rupture Index'].isin(combo)]


>>> hik.ruptures[hik.ruptures['Rupture Index'].isin(combo)]
      Rupture Index  Magnitude  Average Rake (degrees)    Area (m^2)     Length (m)
6395           6395   7.653055                     0.0  4.498414e+09  149947.125000
6446           6446   7.652977                     0.0  4.497603e+09  149920.109375
"""
