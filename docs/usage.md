The code examples below can be run sequentially to provide a quick demo of some solvis useage.

## Opening solutions files

A typical Solvis investigation starts with reading an archive (a zip file) into a solution object.

Composite solutions require selecting an NSHM model version (usually 1.0.4), and constructing a
solution from its source logic tree. A CompositeSolution archive contains the multiple 
FaultSystemSolutions of the complete model.

```py
from pathlib import Path

import nzshm_model as nm
import solvis

model = nm.get_model_version("NSHM_v1.0.4")
composite_solution = solvis.CompositeSolution.from_archive(
    Path("NSHM_v1.0.4_CompositeSolution.zip"), model.source_logic_tree
)
solution = composite_solution.get_fault_system_solution('CRU')
```

If you wish to obtain the default **NSHM_v1.0.4_CompositeSolution.zip** archive,
contact <a href="mailto:nshm@gns.cri.nz">nshm@gns.cri.nz</a>

Depending on the archive type, you will need to use one of:

- [`FaultSystemSolution.from_archive(instance_or_path)`][solvis.solution.fault_system_solution.FaultSystemSolution.from_archive]
- [`InversionSolution.from_archive(instance_or_path)`][solvis.solution.inversion_solution.InversionSolution.from_archive]
- [`CompositeSolution.from_archive(instance_or_path, slt)`][solvis.solution.composite_solution.CompositeSolution.from_archive]

## Manipulating solutions

The Solvis API is consistent over both solution classes (InversionSolution and FaultSystemSolution) 
e.g. Filters, Participation calculations, exporting. 

### Filtering solutions
Solvis provides several **Filter** classes with useful methods for selecting subsets of solutions data.
Take a look at the [filter](../api/filter) package for details and more examples.

```py
from solvis import filter
# ruptures on any of faults A, B, with magnitude and rupture rate limits
rupture_ids = filter.FilterRuptureIds(solution)\
   .for_parent_fault_names(['Alpine: Jacksons to Kaniere', 'Vernon 1' ])\
   .for_magnitude(7.0, 8.0)\
   .for_rupture_rate(1e-6, 1e-2)
```

Filter methods are both chainable, and "set-like" , supporting the usual python set operations (e.g. union, intersection, difference).

### DataFrame APIs

Solvis is designed to work well with [Pandas](https://pandas.pydata.org/) and [Geopandas](https://geopandas.org/) libraries. 
Many solvis methods return either a [Dataframe](https://pandas.pydata.org/docs/reference/frame.html) object or 
primitives to ease working with these APIs.

Solvis also uses the [Pandera](https://pandera.readthedocs.io/en/stable/index.html) library to document and validate 
its dataframes, columns, and types. Check out [dataframe_models](./api/solution/dataframe_models.md) for details of solvis dataframes.

```py
# get the rupture_with_rupture_rates dataframe
rr = solution.model.ruptures_with_rupture_rates

# and filter using pandas ...
filtered_rates_df = rr[rr["Rupture Index"].isin(rupture_ids)]
```

```py
>>> filtered_rates_df
                           fault_system  Rupture Index  rate_max  rate_min  rate_count  rate_weighted_mean  Magnitude  Average Rake (degrees)    Area (m^2)     Length (m)
fault_system Rupture Index
CRU          5539                   CRU           5539  0.000009  0.000003           6            0.000001    7.89999              171.662399  5011800064.0    237245.0625
             6119                   CRU           6119  0.000015  0.000004          12            0.000002   7.899568              171.654221  5006938112.0   236916.59375
             9675                   CRU           9675  0.000123  0.000026          12            0.000020   7.897125              169.483078  4978848256.0  228672.796875
             9680                   CRU           9680  0.000101  0.000031           6            0.000016   7.998456              167.489822  6287248896.0   284855.15625
             12148                  CRU          12148  0.000015  0.000005           6            0.000002   7.779795              170.363174  3800133120.0  175578.703125
...                                 ...            ...       ...       ...         ...                 ...        ...                     ...           ...            ...
             50398                  CRU          50398  0.000148  0.000046           6            0.000007   7.994758              146.645752  6233926144.0   279055.96875
             51682                  CRU          51682  0.000033  0.000006          12            0.000006   7.998924              144.560715  6294017024.0    278447.6875
             56063                  CRU          56063  0.000021  0.000006           6            0.000003   7.992944              148.203522  6207948800.0   268112.59375
             96787                  CRU          96787  0.000083  0.000003          12            0.000003   7.789299              159.564758  3884215040.0  171120.703125
             373612                 CRU         373612  0.000043  0.000020           6            0.000007   7.216816              -177.52005  1039487104.0    43913.53125

[107 rows x 10 columns]
>>>
```

### Support Utilities

 - the [geometry](./api/solvis/geometry.md) module provides methods for handling fault geometries in 2D and 3D.
 - the [solution_participation](./api/solution/solution_participation.md) module provides functions to calculate
    how fault sections, parent faults and named faults are involved in ruptures events.
 - the [solution_surfaces_builder](./api/solution/solution_surfaces_builder.md) module provides methods returning GeoDataframe objects suitable for 
   rendering in common visualisation tools (ArcGIS, Mapbox, etc)

## Outputs

After filtering, data can be written out to CSV for use in other tools:

```py
filtered_rates_df.to_csv("filtered_rupture_rates.csv" )
```

Magnitude-Frequency Distribution (MFD) histogram data can also be
generated and saved:

## Calculate an MFD with Pandas

```py
import pandas as pd
bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
mfd = filtered_rates_df.groupby(
    pd.cut(
        filtered_rates_df.Magnitude,
        bins=bins,
    ))["rate_weighted_mean"].sum(numeric_only=False)
mfd.to_csv( "NSHM_filtered_mfd.csv")
```

## Plot it using Matplotlib

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

plot = plot_mfd(mfd, title="A Filtered MFD")
plot.savefig("A filtered MFD plot.png")
plot.close()
```