from zipfile import Path
import pandas as pd
import geopandas as gpd

class InversionSolution:

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
        self._ruptures_with_rates = None

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

        #set property
        self._rupture_sections = df2
        return self._rupture_sections

    @property
    def rs_with_rates(self):
        if not  self._rs_with_rates is None:
            return self._rs_with_rates
        #df_rupt_rate = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        self._rs_with_rates = self.rupture_sections.join(self.ruptures_with_rates, 'rupture')
        return self._rs_with_rates

    @property
    def ruptures_with_rates(self):
        if not  self._ruptures_with_rates is None:
            return self._ruptures_with_rates
        self._ruptures_with_rates = self.ruptures.join(self.rates.drop(self.rates.iloc[:, :1], axis=1))
        return self._ruptures_with_rates

    #return get the rupture ids for any ruptures intersecting the polygon
    def get_ruptures_intersecting(self, polygon):
        q0 = gpd.GeoDataFrame(self.fault_sections)
        q1 = q0[q0['geometry'].intersects(polygon)] #whitemans_0)]
        sr = self.rs_with_rates
        qdf = sr.join(q1, 'section', how='inner')
        return qdf.rupture.unique()

    def get_ruptures_for_parent_fault(self, parent_fault_name: str):
        # sr = sol.rs_with_rates
        # print(f"Sections with rate (sr_, where parent fault name = '{parent_fault_name}'.")
        sects = self.fault_sections[self.fault_sections['ParentName']==parent_fault_name]
        qdf = self.rupture_sections.join(sects, 'section', how='inner')
        return qdf.rupture.unique()