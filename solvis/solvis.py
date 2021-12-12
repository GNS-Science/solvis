#!python3

from pathlib import PurePath
from zipfile import Path
#from solvis.config import WORK_PATH
from config import WORK_PATH
import pandas as pd

class Solution:

    def __init__(self, archive_path):
        """
        create an opensha modular archive, given a full archive path
        """
        assert Path(archive_path, at='ruptures/indices.csv').exists()
        self._archive_path = archive_path
        self._rates = None
        self._ruptures = None
        self._rupture_props = None
        self._rupture_sections = None
        self._indices = None
        self._rs_with_rates = None

    def _get_dataframe(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = pd.read_csv(Path(self._archive_path, at=path).open()).convert_dtypes()
        return prop

    @property
    def rates(self):
        return self._get_dataframe(self._rates, 'solution/rates.csv')

    @property
    def ruptures(self):
        return self._get_dataframe(self._ruptures, 'ruptures/properties.csv')


    @property
    def indices(self):
        return self._get_dataframe(self._indices, 'ruptures/indices.csv')

    @property
    def rupture_sections(self):

        if not  self._rupture_sections is None:
            return self._rupture_sections

        rs = self.indices #_get_dataframe(self._rupture_sections, 'ruptures/indices.csv').copy()

        #remove "Rupture Index, Num Sections" column
        df_table = rs.drop(rs.iloc[:, :2], axis=1)

        #convert to relational table, turning headings index into plain column
        df2 = df_table.stack().reset_index()

        #remove the headings column
        df2.drop(df2.iloc[:, 1:2], inplace=True, axis=1)
        df2.set_axis(['rupture', 'section'], axis='columns', inplace=True)

        #return df2
        #set property
        self._rupture_sections = df2
        return self._rupture_sections

    @property
    def rs_with_rates(self):
        if not  self._rs_with_rates is None:
            return self._rs_with_rates
        df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.rupture_sections.join(df_rupt_rate, 'rupture')
        return self._rs_with_rates

name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTUzNm9KUmJn.zip"
sol = Solution(PurePath(WORK_PATH,  name))

if __name__ == "__main__":

    sr = sol.rs_with_rates

    print("rupture_sections")
    print(sol.rupture_sections)

    #example queries
    print()

    print("Query: sr[sr['rupture']==5]")
    print(sr[sr['rupture']==5])
    print()

    print("Query: sr[(sr['section']==1010) & (sr['Magnitude']<7.5)].count()")
    print(sr[(sr['section']==1010) & (sr['Magnitude']<7.5)].count())
    print()

    print("sr[(sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count()")
    print(sr[(sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count())
    print()


