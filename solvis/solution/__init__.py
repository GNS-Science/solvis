"""A package for analysis of Opensha Inversion Solutions.

It provides python developers with easy access to the solution data in pandas dataframes.

It supports Aggregation of InversionSolutions as FaultSystemSolutions. It also provides support for NSHM
Source Logic Tree (SLT) and PSHA models.

Classes:
 InversionSolution: handles the standard output of an OpenSHA grand inversion.
 FaultSystemSolution: a aggregation of multiple InversionSolutions sharing the same rupture set.
 CompositeSolution: the container class for complete model and logic tree.
 SolutionParticipation: a helper class to calculate rupture participation for parts of the fault system.

Modules:
 typing: defines class interfaces using `typing.Protocol`
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
from .inversion_solution import InversionSolution, InversionSolutionFile, data_to_zip_direct
from .solution_participation import SolutionParticipation

"""
Notes:
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
