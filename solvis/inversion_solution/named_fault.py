# named_fault.py
"""
A module to produce a named_fault for use with filtering crustal ruptures.

for NSHM_V.1 the Crustal Rupture Sets all use the same Fault Model (form the NZ CFM) 

"""
import csv
import pandas as pd
from typing import Set, Protocol

# from solvis.inversion_solution import FaultSystemSolution, InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

CFM_1_0A_DOM_SANSTVZ_MAP = 'resources/named_faults/cfm_1_0A_no_tvz.xml.FaultsByNameAlt.txt'

csv_list = csv.reader(open(RESOURCE_FILE, mode='r', encoding='utf-8-sig'), delimiter='\t')
df = pd.DataFFrame(cf)

#### Some candidate code for discussion....
class FaultSectionIdFilter():
    """
    A class to filter fault_sections based on criteria and return qualifying section_ids
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution

    def ids_for_named_faults(self, named_fault_names: Set[str]):
        pass

    def ids_for_parent_faults(self, named_fault_names: Set[str]):
        pass

    def ids_for_ruptures(self, rupture_ids: Set[int]):
        pass

    def ids_within_polygon(self, polygon, contained=True):
        pass

class RuptureIdFilter():
    """
    A class to filter ruptures, returning the qualifying rupture_ids.
    """

    def __init__(self, solution: InversionSolutionProtocol):
        self._solution = solution

    def ids_for_named_faults(self, named_fault_names: Set[str]) -> Set[int]:
        """Find ruptures that occur on any of the given named_fault names.

        Args:
            named_fault_names: A list of one or more `named_fault` names.

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `named_fault_names` argument is not valid.
        """
        pass

    def ids_for_parent_faults(self, parent_fault_names: Set[str]) -> Set[int]:
        """Find ruptures that occur on any of the given parent_fault names.

        Args:
            parent_fault_names: A list of one or more `parent_fault` names.

        Returns:
            The rupture_ids matching the filter.

        Raises:
            ValueError: If any `parent_fault_names` argument is not valid.
        """
        df0 = self._fss.fault_sections

        # validate the names ....
        all_parent_names = set(df0['ParentName'].unique().tolist())
        unknown = parent_fault_names.difference(all_parent_names)
        if unknown:
            raise ValueError(f"the solution {self._solution} does not contain the parent_fault_names: {unknowns}.")

        ids = df0[df0['ParentName'].isin(list(parent_fault_names))]['ParentID'].tolist()
        return set([int(id) for id in ids])

    def ids_for_fault_sections(self, fault_section_ids: Set[int]) -> Set[int]:
        """Find ruptures that occur on any of the given fault_section_ids.

        Args:
            fault_section_ids: A list of one or more fault_section ids.

        Returns:
            The rupture_ids matching the filter.
        """
        pass

    def ids_for_rupture_rate(self, min_rate: Optional[float] = None, max_rate: Optional[float] = None):
        """Find ruptures that occur within given rates bounds.

        Args:
            min_rate: The minumum rupture _rate bound.
            max_rate: The maximum rupture _rate bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        pass

    def ids_for_magnitude(self, min_mag: Optional[float] = None, max_mag: Optional[float] = None):
        """Find ruptures that occur within given magnitude bounds.

        Args:
            min_mag: The minumum rupture magnitude bound.
            max_mag: The maximum rupture magnitude bound.

        Returns:
            The rupture_ids matching the filter arguments.
        """
        pass

    def ids_within_polygon(self, polygon, contained=True):
        pass




# def fault_section_ids_for(fault_section_filter: lambda: x fault_names(self, fault_names: Set[str]):
#     '''alias fn'''
#     return self.ids_for_parent_fault_names(fault_names)



# def fault_section_ids_for_named_faults(named_faults: Set[str]):
#     """
#     get the fault_section.ids for the given named_faults.
#     """

def ids_for_parent_fault_names(self, named_faults: Set[str]) -> Set[int]:
    """
    get the fault_section.ids for the given named_faults.
    """
    df0 = self._fss.fault_sections
    # print("fault_sections")
    # print(df0[["ParentID", "ParentName"]])
    ids = df0[df0['ParentName'].isin(list(fault_names))]['ParentID'].tolist()
    return set([int(id) for id in ids])
