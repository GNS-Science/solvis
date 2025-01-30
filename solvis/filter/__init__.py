r"""
This package provides classes to support filtering by key attributes of the solution classes.

 - [FaultSystemSolution][solvis.solution.fault_system_solution.FaultSystemSolution] aggregated solutions
 - [InversionSolution][solvis.solution.inversion_solution.InversionSolution] individual solutions

Classes:
  FilterParentFaultIds: for filtering solution parent faults.
  FilterRuptureIds: for filtering solution ruptures.
  FilterSubsectionIds: (subsection_id_filter.md/#solvis.filter.subsection_id_filter.FilterSubsectionIds)

Examples:
    ```py
    >>> solution = InversionSolution.from_archive(filename)
    >>> model = solution.model
    >>> parent_fault_ids = FilterParentFaultIds(model)\
            .for_parent_fault_names(['Alpine: Jacksons to Kaniere'])\
            .for_rupture_ids([1,2,3])

    >>> rupture_ids = FilterRuptureIds(model)\
            .for_parent_fault_ids(parent_fault_ids)\
            .for_magnitude(7.95, 8.15)

    >>> assert FilterRuptureIds(model)\
            .for_parent_fault_names(['Alpine: Jacksons to Kaniere'])\
            .issuperset(rupture_ids), "using set operands on two `filter.for` results"
    ```

API notes:

The public classes in this package provide similar behaviour to make the API both simple to use and
versatile:

 - The public class methods all return set-like objects, making  it possible to combine results using
`set` operands e.g. `union`, `intersection`, `difference`.

 - The public class methods are 'chainable', so that multiple `for_` method calls can be linked
 together (see example below). The  default join operation is "intersection" so
 that each chained method call is 'refining' results from the prior method call(s).
 This behaviour can be overridden using the `join_prior` argument.
-

"""

from .parent_fault_id_filter import FilterParentFaultIds
from .rupture_id_filter import FilterRuptureIds
from .subsection_id_filter import FilterSubsectionIds
