"""This package exports the **Solvis** analysis library.

This library is designed to facilitate seismic analysis and visualization. 
It includes features related to seismic data processing including filtering,
modeling, and exporting results in formats like GeoJSON.

Classes:
 InversionSolution: handles the standard output of an opensha grand inversion.
 FaultSystemSolution: a aggregation of multiple InversionSolutions sharing the same rupture set.
 CompositeSolution: the container class for complete model and logic tree.
"""
from .solution import CompositeSolution, FaultSystemSolution, InversionSolution

__version__ = '1.0.0-beta-0'
