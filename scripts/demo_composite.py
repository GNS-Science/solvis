# from nzshm_common.location.location import location_by_id
from solvis import geometry, CompositeSolution, FaultSystemSolution, export_geojson
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
>>>hik.ruptures_with_rupture_rates[hik.ruptures_with_rupture_rates['Rupture Index'].isin(combo)]


>>> hik.ruptures[hik.ruptures['Rupture Index'].isin(combo)]
      Rupture Index  Magnitude  Average Rake (degrees)    Area (m^2)     Length (m)
6395           6395   7.653055                     0.0  4.498414e+09  149947.125000
6446           6446   7.652977                     0.0  4.497603e+09  149920.109375
"""


# HISTORY for creating single event solutions for Sanjay
"""
from solvis import geometry, CompositeSolution, FaultSystemSolution, export_geojson
from pathlib import Path
import nzshm_model as nm

slt = nm.get_model_version(nm.CURRENT_VERSION).source_logic_tree()
hik = FaultSystemSolution.from_archive(Path("WORK/HIK_fault_system_solution.zip"))
hik.rupture_rates
hkr = hik.rupture_rates
hkr[hkr["Rupture Index"] == 4912]
hcr = hik.composite_rates
hcr[hcr["Rupture Index"] == 4912]
slt.source_logit_tree()
slt.source_logic_tree()
slt.source_logic_tree
slt
slt
for b in slt.fault_system_lts:
    if b.short_name=="HIK":
        print(b)
from solvis import InversionSolution
hiksol = InversionSolution.from_archive(Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip))
hiksol = InversionSolution.from_archive(Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip"))
sol4912 = hiksol.filter_solution([4912])
import solvis
sol4912 = solvis.filter_solution(hiksol, [4912])
sol4912.rupture_rates
sol4912.ruptures
sol4912.indices
help(sol4912.to_archive)
sol4912.to_archive(Path("WORK/FILTER_HIK/Hikurangi_4912_FilteredSolution.zip"))
help(sol4912.to_archive)
sol4912.to_archive(Path("WORK/FILTER_HIK/Hikurangi_4912_FilteredSolution.zip"), Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip"))
sol4912.to_archive(Path("WORK/FILTER_HIK/Hikurangi_4912_FilteredSolution_opensha_compat_mode.zip"), Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip"), compat=True)
sol7109 = solvis.filter_solution(hiksol, [7109])
sol7109.to_archive(Path("WORK/FILTER_HIK/Hikurangi_7109_FilteredSolution.zip"), Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip"))
sol7109.to_archive(Path("WORK/FILTER_HIK/Hikurangi_7109_FilteredSolution_opensha_compat_mode.zip"), Path("WORK/NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTA3NzEz.zip"), compat=True)
"""
