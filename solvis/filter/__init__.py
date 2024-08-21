"""
The `filter` package provides classes to simplify filtering solutions by
various attributes of InversionSolution:

Classes:
    - .filter.rupture_id_filter.FilterParentFaultIds
    - .filter.rupture_id_filter.FilterRuptureIds
    - .filter.subsection_id_filter.FilterSubsectionIds

Examples:
    ```py
    >>> solution = InversionSolution.from_archive(filename)
    >>> flt_parent_fault_ids = FilterParentFaultIds(solution)
    >>> flt_parent_fault_ids.for_parent_fault_names(['Alpine Jacksons to Kaniere'])
    { 23 }
    ```
"""
