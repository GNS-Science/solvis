"""A module to produce a named_fault for use with filtering crustal ruptures.

for NSHM_V1.* the Crustal Rupture Sets all use the same Fault Model (form the NZ CFM)
"""
import csv
from functools import lru_cache

import pandas as pd

CFM_1_0A_DOM_SANSTVZ_MAP = 'resources/named_faults/cfm_1_0A_no_tvz.xml.FaultsByNameAlt.txt'


@lru_cache
def named_fault_table() -> pd.DataFrame:
    """Build a dataframe from the resoource file."""
    csv_rows = csv.reader(open(CFM_1_0A_DOM_SANSTVZ_MAP, mode='r', encoding='utf-8-sig'), delimiter='\t')

    def reform(row):
        return (row[0], [int(x) for x in row[1:]])

    reformed = [reform(row) for row in csv_rows]
    return pd.DataFrame(reformed, columns=['named_fault_name', 'parent_fault_ids']).set_index('named_fault_name')
