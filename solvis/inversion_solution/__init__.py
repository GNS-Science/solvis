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

Note:

This library uses names that are `imported` from other projects:

  - the NZ CommunityFaultModel (CFM)
  - the Opensha project

and these are extended to form the solvis domain model.

This table explains how some common terms correlate across the three domains:

    - `solvis:subsection`   => Opensha:Fault or FaultSection or SubSection = CFM: (n/a)
    - `solvis:parent_fault` => Opensha:ParentFault => CFM: FaultSection
    - `solvis:named_fault`  => Opensha:NamedFault => CFM: ??
    - `solvis:rupture`      => Opensha:Rupture => CFM: (n/a)
"""

from .composite_solution import CompositeSolution
from .fault_system_solution import FaultSystemSolution
from .inversion_solution import InversionSolution
