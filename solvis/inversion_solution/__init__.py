"""
A package for Inversion Solutions.

For convenience, importing this package includes the following classes by default:

- [`CompositeSolution`][solvis.inversion_solution.CompositeSolution]
- [`FaultSystemSolution`][solvis.inversion_solution.FaultSystemSolution]
- [`InversionSolution`][solvis.inversion_solution.InversionSolution]

Example:
    ```py
    from solvis import inversion_solution
    new_solution = inversion_solution.CompositeSolution.from_archive(new_path, slt)
    ```

"""

from .composite_solution import CompositeSolution
from .fault_system_solution import FaultSystemSolution
from .inversion_solution import InversionSolution
