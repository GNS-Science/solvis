This file is for use in testing where we want a smaller dataset than a full NZ NSHM InversionSolution.

This file TinyInversionSolution.zip was produced as follows:

```
import json
import nzshm_model as nm
import solvis

from solvis.filter import FilterRuptureIds, FilterParentFaultIds, FilterSubsectionIds

solution = solvis.InversionSolution.from_archive("NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTM0.zip")

TARGET_FAULTS = ['Masterton', 'Ohariu', 'Wairarapa: 1', 'Wairarapa: 2', 'Wairarapa: 3', 'Ostler North', 'Ostler South']
ruptures = FilterRuptureIds(solution).for_parent_fault_names(TARGET_FAULTS)
new_solution = solution.filter_solution(solution, rupture_ids=ruptures)
new_solution.to_archive(
    archive_path="TinyInversionSolution.zip",
    base_archive_path="NZSHM22_ScaledInversionSolution-QXV0b21hdGlvblRhc2s6MTEzMTM0.zip",
    compat=True)

```

Some useful metrics from the filtered solution:

  - len(new_solution.model.rupture_sections.section.unique().tolist()) => 159
  - len(new_solution.solution_file.ruptures.index.unique().tolist()) => 37