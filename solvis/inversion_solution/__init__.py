"""
A package for Inversion Solutions and collections of those for use with
Source Logic Tree (SLT) and PSHA models.

Classes:
 InversionSolution: handles the standard output of an opensha grand inversion.
 FaultSystemSolution: a aggregation of multiple InversionSolutions sharing the same rupture set.
 CompositeSolution: the container class for complete model and logic tree.

Modules:
 typing: defines class interfaces using `typing.Protocol`
 inversion_solution: defines the InversionSolution and BranchInversionSolution classes.
 inversion_solution_file: defines a mixin class that manages all IO for an InversionSolution archive.
 inversion_solution_operations: defines a mixin class providing anaysis of InversionSolutions.
 fault_system_solution: defines the aggregation class FaultSystemSolution.
 fault_system_solution_file: defines a mixin class that manages all IO for a FaultSystemSolution archive.
 composite_solution: defines the CompositeSolution class.
 named_fault: helper module for named_faults (used with filtering crustal ruptures).
 solution_surfaces_builder: defines the SolutionSurfacesBuilder class.

Example:
    ```py
    from solvis import inversion_solution
    new_solution = inversion_solution.CompositeSolution.from_archive(new_path, slt)
    ```
"""

from .composite_solution import CompositeSolution
from .fault_system_solution import FaultSystemSolution
from .fault_system_solution_model import FaultSystemSolutionModel
from .inversion_solution import InversionSolution

"""
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
