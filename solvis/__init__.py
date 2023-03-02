from .geometry import circle_polygon
from .inversion_solution import CompositeSolution, InversionSolution
from .solvis import export_geojson, mfd_hist, rupt_ids_above_rate, section_participation, filter_solution

__version__ = '0.4.0'

# alias fn for legacy code
new_sol = filter_solution
