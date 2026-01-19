"""This package exports the **Solvis** analysis library.

This library is designed to facilitate analysis and visualization of OpenSHA inversion solutions.
It includes methods for filtering based on rupture rate, geographic location, and fault involvment.
Results can be exported to multiple formats such as GeoJSON.

Classes:
 InversionSolution: handles the standard output of an opensha grand inversion.
 FaultSystemSolution: a aggregation of multiple InversionSolutions sharing the same rupture set.
 CompositeSolution: the container class for complete model and logic tree.
"""

from . import utils
from .solution import CompositeSolution, FaultSystemSolution, InversionSolution

__version__ = '1.3.1'
