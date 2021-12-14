#!python3

import os
from pathlib import PurePath
from zipfile import Path
#from solvis.config import WORK_PATH
#from config import WORK_PATH
import pandas as pd
import geopandas as gpd
import numpy as np

from shapely.geometry import Polygon

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
        self._fault_sections = None
        self._rs_with_rates = None

    def _get_dataframe(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = pd.read_csv(Path(self._archive_path, at=path).open()).convert_dtypes()
        return prop

    def _get_geojson(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = gpd.read_file(Path(self._archive_path, at=path).open())
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
    def fault_sections(self):
        return self._get_geojson(self._fault_sections, 'ruptures/fault_sections.geojson' )


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



def demo1():
    sr = sol.rs_with_rates
    print("Query: Query: sections with rate (sr) where sr['rupture']==5]")
    print(sr[sr['rupture']==5])
    print()

    print("Query: sections with rate (sr) where (sr['section']==1010) & (sr['Magnitude']<7.5)")
    print(sr[(sr['section']==1010) & (sr['Magnitude']<7.5)].count())
    print()

    print("Count of sections with rate (sr) where (sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count()")
    print(sr[(sr['Annual Rate']>=1e-9) & (sr['Magnitude']<7.5)].count())
    print()

def demo2():
    sr = sol.rs_with_rates
    print("Sections with rate (sr_, where parent fault name = 'Whitemans Valley'.")
    acton_sects = sol.fault_sections[sol.fault_sections['ParentName']=="Whitemans Valley"]
    qry = gpd.GeoDataFrame(sr.join(acton_sects, 'section', how='inner'))
    print(qry)

    print("qry[(qry['Annual Rate']>=1e-9) & (qry['Magnitude']<7.5)]")
    print(qry[(qry['Annual Rate']>=1e-9) & (qry['Magnitude']<7.5)])
    print()

    #Geometry based query

def geom_demo1(polygon):
    #wlg_poly = Polygon([(0,0), (2,0), (2,2), (0,2)])

    sr = sol.rs_with_rates
    q0 = gpd.GeoDataFrame(sol.fault_sections)
    q1 = q0[q0['geometry'].intersects(polygon)] #whitemans_0)]
    qdf = gpd.GeoDataFrame(sr.join(q1, 'section', how='inner'))
    # print("Near Whitemans Valley (Polygon)")
    # print(qdf)
    # print()
    # print("Near Whitemans Valley (Polygon) and (qdf['Annual Rate']>=1e-9) & (qdf['Magnitude']<8.5)")
    # print(qdf[(qdf['Annual Rate']>=1e-9) & (qdf['Magnitude']<8.5)])
    return qdf


def geom_demo2(df_ruptures: pd.DataFrame):
    #https://stackoverflow.com/questions/50655370/filtering-the-dataframe-based-on-the-column-value-of-another-dataframe
    sr = sol.rs_with_rates
    df3 = sr[(sr.rupture.isin(list(df_ruptures.rupture))) & (sr['Annual Rate']>0)]
    # print(df3)

    # print("df3['Annual Rate'].mean()")
    # print(df3['Annual Rate'].mean())
    # print()

    # print("Pivot table (note precision is not lost!!)")
    df4 = df3.pivot_table(values='Annual Rate', index= ['section'], aggfunc=np.sum)
    #df4['Annual Rate'].mean()

    q0 = gpd.GeoDataFrame(sol.fault_sections)
    #df5 = gpd.GeoDataFrame(df4.join(sr, 'section', how='inner', lsuffix='_agg'))
    df6 = df4.join(q0, 'section', how='inner')
    return df6


def histo(df: pd.DataFrame):
    #https://stackoverflow.com/questions/45273731/binning-a-column-with-python-pandas
    bins = [round(x/100, 2) for x in range(700, 730, 1)]


def export_geojson(gdf: gpd.GeoDataFrame, filename):
    print(f"Exporting to {filename}")
    f = open(filename, 'w')
    f.write(gdf.to_json())
    f.close()


whitemans_0 = Polygon([(174.892,-41.3), (174.9, -41.345), (174.91, -41.33), (174.922, -41.32), (174.9360, -41.298)])

nap_hast = Polygon([ (176.7563, -39.4468),
                    (177.0886,-39.4426 ),
                    (177.1078, 39.7220),
                    (176.7563, -39.7178),
                    (176.7563, -39.4468)
                    ])

wlg_hex = Polygon([ (175.5780, -40.5472),
                     (176.1053, -41.2902),
                     (175.3418, -42.0656),
                     (174.0839, -42.0411),
                     (173.4357, -41.3315),
                     (174.1223, -40.5305),
                     (175.5780, -40.5472)
                     ])

#name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTUzNm9KUmJn.zip"
# 60m
name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTc1MlBDZllC.zip"
# 60hrs
#name = "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6NTkzMHJ0YWJU.zip"

WORK_PATH = os.getenv('NZSHM22_SCRIPT_WORK_PATH', PurePath(os.getcwd(), "tmp"))

sol = Solution(PurePath(WORK_PATH,  name))


if __name__ == "__main__":

    # print(sol.fault_sections)

    # sr = sol.rs_with_rates
    # print("rupture_sections")
    # print(sol.rupture_sections)

    # #example queries
    # print()
    # print("Done")
    wlg1 = geom_demo1(wlg_hex)
    wlg2 = geom_demo2(wlg1[wlg1['Annual Rate']>1e-6])
    export_geojson(gpd.GeoDataFrame(wlg2), "wlg_hex_60m_rate_above_1e-6.geojson")