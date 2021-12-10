#!python3

from pathlib import PurePath
from zipfile import Path
from config import WORK_PATH
import pandas as pd


class Solution:

    def load(self, archive_path):
        """
        load an opensha modular archive, given a full path

        """
        rates = Path(archive_path, at='solution/rates.csv')

        assert rates.exists()
        self._path = archive_path,
        self.rates = rates
        self.rupture_props = Path(archive_path, at='ruptures/properties.csv')
        self.rupture_sections = Path(archive_path, at='ruptures/indices.csv')
        self.fault_sections = Path(archive_path, at='ruptures/fault_sections.geojson')

        return self

def from_solution(solution):

    ruptures = pd.read_csv(solution.rupture_props.open())

    sections = pd.read_csv(solution.rupture_sections.open())
    print("ruptures")
    print(ruptures)
    print("sections")
    print(sections)
    return
    return pd.read_csv(solution.rupture_props.open())

if __name__ == "__main__":

    name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTUzNm9KUmJn.zip"

    sol = Solution().load(PurePath(WORK_PATH,  name))
    print( sol, sol._path)

    print( from_solution(sol))
    # rates = sol.rates.open()
    #for line in sol.rupture_props.open().readlines():
    #   print(line)
