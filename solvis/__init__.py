"""
The base Solvis analysis package.

For convenience, importing this package will also import the following functions
and classes by default:

- From [solvis.geometry][]:
    - [`circle_polygon`][solvis.geometry.circle_polygon]
- From [solvis.inversion_solution][]:
    - [`CompositeSolution`][solvis.inversion_solution.CompositeSolution]
    - [`FaultSystemSolution`][solvis.inversion_solution.FaultSystemSolution]
    - [`InversionSolution`][solvis.inversion_solution.InversionSolution]
- From [solvis.filter][]:
    - [`FilterParentFaultIds`]solvis.filter.rupture_id_filter.FilterParentFaultIds]
    - [`FilterRuptureIds`][solvis.filter.rupture_id_filter.FilterRuptureIds]
    - [`FilterSubsectionIds`][solvis.filter.subsection_id_filter.FilterSubsectionIds]
- From [solvis.solvis][]:
    - [`export_geojson`][solvis.solvis.export_geojson]
    - [`mfd_hist`][solvis.solvis.mfd_hist]
    - [`parent_fault_names`][solvis.solvis.parent_fault_names] (deprecated)
    - [`rupt_ids_above_rate`][solvis.solvis.rupt_ids_above_rate]
    - [`section_participation`][solvis.solvis.section_participation]

Example:
    ```py
    >>> import solvis
    >>> solvis.circle_polygon(50000, -37.78, 175.28)  # 50km radius around Hamilton
    <POLYGON ((175.849 -37.779, 175.847 -37.823, 175.839 -37.866, 175.825 -37.90...>
    ```
"""


import importlib

from .geometry import circle_polygon
from .inversion_solution import CompositeSolution, FaultSystemSolution, InversionSolution
from .solvis import export_geojson, mfd_hist, parent_fault_names, rupt_ids_above_rate, section_participation

# # from solvis.filter.subsection_id_filter import FilterSubsectionIds
# def __getattr__(name):
#     if name == 'FilterRuptureIds':
#         return importlib.import_module('solvis.filter.rupture_id_filter').FilterRuptureIds
#     if name == 'FilterParentFaultIds':
#         return importlib.import_module('solvis.filter.parent_fault_id_filter').FilterParentFaultIds
#     if name == 'FilterSubsectionIds':
#         return importlib.import_module('solvis.filter.subsection_id_filter').FilterSubsectionIds


__version__ = '0.12.3'
