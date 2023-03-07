from .geometry import circle_polygon
from .inversion_solution import CompositeSolution, FaultSystemSolution, InversionSolution
from .solvis import export_geojson, filter_solution, mfd_hist, rupt_ids_above_rate, section_participation

__version__ = '0.4.0'

# alias fn for legacy code
new_sol = filter_solution
