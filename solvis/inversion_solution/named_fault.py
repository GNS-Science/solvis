# flake8: noqa  this is WIP
# type: ignore
# named_fault.py
"""
A module to produce a named_fault for use with filtering crustal ruptures.

for NSHM_V.1 the Crustal Rupture Sets all use the same Fault Model (form the NZ CFM) 

"""
import csv
from typing import Protocol, Set

import pandas as pd

# from solvis.inversion_solution import FaultSystemSolution, InversionSolution
from solvis.inversion_solution.typing import InversionSolutionProtocol

CFM_1_0A_DOM_SANSTVZ_MAP = 'resources/named_faults/cfm_1_0A_no_tvz.xml.FaultsByNameAlt.txt'

csv_list = csv.reader(open(RESOURCE_FILE, mode='r', encoding='utf-8-sig'), delimiter='\t')
df = pd.DataFFrame(cf)


def ids_for_parent_fault_names(self, named_faults: Set[str]) -> Set[int]:
    """
    get the fault_section.ids for the given named_faults.
    """
    df0 = self._fss.fault_sections
    # print("fault_sections")
    # print(df0[["ParentID", "ParentName"]])
    ids = df0[df0['ParentName'].isin(list(fault_names))]['ParentID'].tolist()
    return set([int(id) for id in ids])
