# solvis

[![pypi](https://img.shields.io/pypi/v/solvis.svg)](https://pypi.org/project/solvis/)
[![python](https://img.shields.io/pypi/pyversions/solvis.svg)](https://pypi.org/project/solvis/)
[![Build Status](https://github.com/GNS-Science/solvis/actions/workflows/dev.yml/badge.svg)](https://github.com/GNS-Science/solvis/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/GNS-Science/solvis/branch/main/graphs/badge.svg)](https://codecov.io/github/GNS-Science/solvis)


* Documentation: <https://GNS-Science.github.io/solvis>
* GitHub: <https://github.com/GNS-Science/solvis>
* PyPI: <https://pypi.org/project/solvis/>
* Free software: GPL-3.0-only

# Features / Goals

 - analysis of opensha modular solution files.
 - opensha modular documentation
 - pandas, geopanda references

From a typical modular opensha Inversion Solution archive, we want to produce views that allow deep exploration 
of the solution and rupture set characteristics. Features:

 - [ ] user can choose from regions already defined in the solution
 - user can select ruptures matching 
    - [x] parent fault
    - [ ] named fault (fault system)
    - [ ] constraint region (from TargetMFDs)
 - [x] user can create new region polygons
 - [ ] user can compare selections (e.g. Wellington East vs Wellington CBD vs Hutt Valley) 
 - for a given query result show me dimensions...
    - mag, length, area, rate, section count, parent fault count, ~jump-length, jump angles~, slip (various), partication, nucleation 
    - filter, group on any of the dimensions


## From here the user can answer questions like ....

 - create a MFD histogram in 0.01 bins from 7.0 to 7.30 (3O bins) for the WHV fault system
 - list all ruptures between 7.75 and 8.25, ordered by rupture-length
 - given a user-defined-function udf RuptureComplexity(rupture) rank ruptures in Region X by complexity, then by magnitude

  - regional MFD
      - [x] participation (sum of rate) for every rupture though a point
      - [ ] nucleation/blame/culpability rate summed over the region
           normalised by the area of an area (region, named fault)


## Install (Linux, OSX)

```
poetry add solvis
```

### Windows Installation with pipwin (CHECK)

This information predates poetry and has not been check since ...

You will have to delete the fiona and shapely lines from requirements.txt, then run the following lines:
pip3 install -r requirements

```commandline
pip install pipwin
pipwin install gdal
pipwin install fiona
pipwin install shapely
pip install -r requirements.txt
```

## Run

```
python3 -m demo

or python3 demo.py
```

## Plotting


f = plt.figure()
#nx = int(f.get_figwidth() * f.dpi)
#ny = int(f.get_figheight() * f.dpi)
f.figimage(data)
plt.show()