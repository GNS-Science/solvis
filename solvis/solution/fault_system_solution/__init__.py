"""
A package supporting aggregation of compatible InversionSolutions via the FaultSystemSolution class.

Modules:
 fault_system_solution: defines the aggregation class FaultSystemSolution.
 fault_system_solution_file: defines a class that manages all IO for a FaultSystemSolution archive.
 fault_system_solution_model: defines a class providing anaysis of FaultSystemSolution.
"""

from .fault_system_solution import FaultSystemSolution
from .fault_system_solution_model import FaultSystemSolutionModel
