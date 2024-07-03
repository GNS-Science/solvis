# Installation

Solvis is intended to be used in the context of spatial data analysis,
and as such has dependencies on libraries like
[NumPy](https://pypi.org/project/numpy/),
[GeoPandas](https://pypi.org/project/geopandas/).

Solvis requires Python, and at the time of writing supports the following
versions:

[![python](https://img.shields.io/pypi/pyversions/solvis.svg)](https://pypi.org/project/solvis/)

Depending on your use case, you may also wish to install
[Shapely](https://pypi.org/project/shapely/)
and
[PyVista](https://pypi.org/project/pyvista/)
for certain functions (e.g.
[`geometry.section_distance`][solvis.geometry.section_distance].)

For easy package installation, either [pip][] or [poetry][] is recommended.

## Stable release

A stable release of the Solvis package can be installed from the Python Package
Index (PyPI).


### Using pip

```console
$ pip install solvis
```

Or to include scripts dependencies and PyVista with the Visualization Toolkit (VTK):
```console
$ pip install solvis[scripts,vtk]
```

### Adding to a poetry project

```console
$ poetry add solvis
```

or to include the extras:

```console
$ poetry add solvis[scripts,vtk]
```


## From source code

The source code for `solvis` can be downloaded from the [Github repository][].

You can clone down the public repository with:

```console
$ git clone https://github.com/GNS-Science/solvis.git
```

Once you have a copy of the source, you can install the package into your
Python environment:

```console
$ pip install .
```

Or with Poetry (using `--all-extras` to install all extra dependencies is
recommended for development):
```console
$ poetry install --all-extras
```


[poetry]: https://python-poetry.org/
[pip]: https://pip.pypa.io
[Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
[Github repository]: https://github.com/GNS-Science/solvis
