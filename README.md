# Solvis
A library to support the analysis of [OpenSHA](https://opensha.org/) inversion solution data.

[![pypi](https://img.shields.io/pypi/v/solvis.svg)](https://pypi.org/project/solvis/)
[![python](https://img.shields.io/pypi/pyversions/solvis.svg)](https://pypi.org/project/solvis/)
[![Build Status](https://github.com/GNS-Science/solvis/actions/workflows/dev.yml/badge.svg)](https://github.com/GNS-Science/solvis/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/GNS-Science/solvis/branch/main/graphs/badge.svg)](https://codecov.io/github/GNS-Science/solvis)

Solvis is used in the geospatial investigation of the New Zealand
[National Seismic Hazard
Model](https://www.gns.cri.nz/research-projects/national-seismic-hazard-model/)
inversion sources and rates. It supports both individual inversions
and the composite model.

* Documentation: <https://GNS-Science.github.io/solvis>
* GitHub: <https://github.com/GNS-Science/solvis>
* PyPI: <https://pypi.org/project/solvis/>
* Free software: GNU Affero General Public License v3.0

# Features / Goals

Solvis is used in the analysis of OpenSHA
[Modular Fault System Solution](https://opensha.org/Modular-Fault-System-Solution) files.

From a typical modular OpenSHA Inversion Solution archive, we can produce views that
allow deep exploration of the solution and rupture set characteristics.

- Select a set of ruptures matching:
    - one or more parent faults
    - one or more corupture fault names
    - the vicinity of one or more named `nzshm-common` locations
    - defined regions
- Create new region polygons
- Determine geometric features, such as dip direction relative to strike bearing
- Calculate the geometries of solution and fault surfaces projected onto the Earth surface
- Calculate fault sections with their rupture rates and solution slip rates
- Generate Magnitude-Frequency Distribution (MFD) histogram data


## Install (Linux, WSL, OSX)

See [Installation](docs/installation.md) instructions.
