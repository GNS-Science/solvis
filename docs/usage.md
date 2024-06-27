# Usage

If you wish to obtain the default **NSHM_v1.0.4_CompositeSolution.zip** archive,
contact <a href="mailto:nshm@gns.cri.nz">nshm@gns.cri.nz</a>


## Reading data

A typical Solvis investigation starts with reading an archive into a solution object.

Depending on the data type, you will need to use one of:

- [`FaultSystemSolution.from_archive(instance_or_path)`][solvis.inversion_solution.fault_system_solution.FaultSystemSolution.from_archive]
- [`InversionSolution.from_archive(instance_or_path)`][solvis.inversion_solution.inversion_solution.InversionSolution.from_archive]
- [`CompositeSolution.from_archive(instance_or_path, slt)`][solvis.inversion_solution.composite_solution.CompositeSolution.from_archive]

Composite solutions require selecting an NSHM model version (usually 1.0.4), and constructing a
solution from its source logic tree.

```py
from pathlib import Path

import nzshm_model as nm
import solvis

model = nm.get_model_version("NSHM_v1.0.4")
slt = model.source_logic_tree()
composite_solution = solvis.CompositeSolution.from_archive(
    Path("NSHM_1.0.4_CompositeSolution.zip"), slt
)
```

## Refining solution data

To gather rupture IDs from a fault system solution:

```py
fault_system_solution = composite_solution.get_fault_system_solution("CRU")
```

Refining to a specific set of rupture IDs:

```py
rupture_ids = fault_system_solution.get_rupture_ids_for_location_radius(
    ["WLG"],  # Around Wellington
    5,        # 5km
)
```

Or intersecting an arbitrary polygon:
```py
polygon_rupture_ids = fault_system_solution.get_rupture_ids_intersecting(
    my_polygon  # A Shapely geometry Polygon
)
```

The set of rupture IDs can then be used as a filter of the rupture dates data
frame.

```py
# filter the rupture_with_rates dataframe
rr = fault_system_solution.ruptures_with_rupture_rates
filtered_rates = rr[rr["Rupture Index"].isin(list(rupture_ids))]
```

## Outputs

After filtering, data can be written out to CSV for use in other tools
(choose your own `output_folder` Path):

```py
filtered_rates.to_csv(output_folder / "NSHM_1.0.4_WLG_5k_ruptures.csv")

```

Magnitude-Frequency Distribution (MFD) histogram data can also be
generated and saved:

```py
import pandas as pd
bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
mfd = filtered_rates.groupby(
    pd.cut(
        filtered_rates.Magnitude,
        bins=bins,
    ))["rate_weighted_mean"].sum(numeric_only=False)
mfd.to_csv(output_folder / "NSHM_1.0.4_WLG_5k_mfd.csv")
```

And with `matplotlib`, charts generated:

```py
import matplotlib.pyplot as plt
import numpy as np

def plot_mfd(mfd: pd.DataFrame, title: str = "Title"):
    mag = [a.mid for a in mfd.index]
    rate = np.asarray(mfd)
    rate[rate == 0] = 1e-20  # set minimum rate for log plots
    fig = plt.figure()
    fig.set_facecolor("white")
    plt.title(title)
    plt.ylabel("Incremental Rate ($yr^-1$)")
    plt.xlabel("Magnitude")
    plt.semilogy(mag, rate, color="red")
    plt.axis([6.0, 9.0, 0.000001, 1.0])
    plt.grid(True)
    return plt

plot = plot_mfd(mfd, title="NSHM_1.0.4 WLG 5k MFD")
plot.savefig(output_folder / "NSHM_1.0.4_WLG_5k_mfd_plot.png")
plot.close()
```
