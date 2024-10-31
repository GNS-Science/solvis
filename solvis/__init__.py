"""
The base Solvis analysis package.

Classes:
 InversionSolution: handles the standard output of an opensha grand inversion.
 FaultSystemSolution: a aggregation of multiple InversionSolutions sharing the same rupture set.
 CompositeSolution: the container class for complete model and logic tree.

Methods:
 circle_polygon: a polygon builder.
 export_geojson: solvis.solvis.export_geojson
 mfd_hist: [solvis.solvis.mfd_hist]
 parent_fault_names: [solvis.solvis.parent_fault_names] (deprecated)
 rupt_ids_above_rate: solvis.solvis.rupt_ids_above_rate] (deprecated)
 section_participation: solvis.solvis.section_participation] (deprecated)

Example:
    ```py
    >>> import solvis
    >>> solvis.circle_polygon(50000, -37.78, 175.28)  # 50km radius around Hamilton
    <POLYGON ((175.849 -37.779, 175.847 -37.823, 175.839 -37.866, 175.825 -37.90...>
    ```
"""
# from .solution.fault_system_solution import
from .geometry import circle_polygon
from .solution import CompositeSolution, FaultSystemSolution, InversionSolution
from .solvis import export_geojson, mfd_hist

__version__ = '0.12.3'
