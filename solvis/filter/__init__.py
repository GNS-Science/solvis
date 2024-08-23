"""
The `filter` package provides classes to filter solutions by
various attributes of InversionSolution:

Classes:
    FilterParentFaultIds
    FilterRuptureIds
    FilterSubsectionIds

Examples:
    ```py
    >>> solution = InversionSolution.from_archive(filename)
    >>> flt_parent_fault_ids = FilterParentFaultIds(solution)
    >>> flt_parent_fault_ids\
            .for_parent_fault_names(['Alpine Jacksons to Kaniere'])
            #CHAINING NOT SUPPORTED YET .. can we do it?? for_rupture_ids([1,2,3])
    { 23 }
    ```
"""
from .parent_fault_id_filter import FilterParentFaultIds
from .rupture_id_filter import FilterRuptureIds
from .subsection_id_filter import FilterSubsectionIds
