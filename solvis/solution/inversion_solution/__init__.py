"""A package for the analysis of OpenSHA InversionSolution archives.

These are the zip archives produced as the output of an OpenSHA grand inversion.

Modules:
 inversion_solution: defines the InversionSolution and BranchInversionSolution classes.
 inversion_solution_file: defines a mixin class that manages all IO for an InversionSolution archive.
 inversion_solution_model: defines a mixin class providing anaysis of InversionSolutions.
"""

from .inversion_solution import BranchInversionSolution, InversionSolution
from .inversion_solution_file import InversionSolutionFile, data_to_zip_direct
from .inversion_solution_model import InversionSolutionModel
