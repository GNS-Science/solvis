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
- From [solvis.solvis][]:
    - [`export_geojson`][solvis.solvis.export_geojson]
    - [`mfd_hist`][solvis.solvis.mfd_hist]
    - [`parent_fault_names`][solvis.solvis.parent_fault_names]
    - [`rupt_ids_above_rate`][solvis.solvis.rupt_ids_above_rate]
    - [`section_participation`][solvis.solvis.section_participation]

Example:
    ```py
    >>> import solvis
    >>> solvis.circle_polygon(50000, -37.78, 175.28)  # 50km radius around Hamilton
    <POLYGON ((175.849 -37.779, 175.847 -37.823, 175.839 -37.866, 175.825 -37.90...>
    ```
"""

from .geometry import circle_polygon
from .inversion_solution import CompositeSolution, FaultSystemSolution, InversionSolution
from .solvis import export_geojson, mfd_hist, parent_fault_names, rupt_ids_above_rate, section_participation

__version__ = '0.12.1'
