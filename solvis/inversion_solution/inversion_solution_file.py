import json
import time
import zipfile
from pathlib import Path
from typing import Any, List

import geopandas as gpd
import pandas as pd

from .typing import InversionSolutionProtocol


def data_to_zip_direct(z, data, name):
    zinfo = zipfile.ZipInfo(name, time.localtime()[:6])
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zinfo, data)


WARNING = """
# Attention

This Inversion Solution archive has been modified
using the solvis python library.

Data may have been filtered out of an original
Inversion Solution archive file:
 - 'solution/rates.csv'
 - 'ruptures/properties.csv'
 - 'ruptures/indices.csv'

"""


def reindex_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    new_df = dataframe.copy().reset_index(drop=True).drop(columns=['Rupture Index'])  # , errors='ignore')
    new_df.index = new_df.index.rename('Rupture Index')
    # print("NEW DF", new_df)
    return new_df


class InversionSolutionFile(InversionSolutionProtocol):
    """
    Class to handle the opensha modular archive file form
    """

    RATES_PATH = 'solution/rates.csv'
    RUPTS_PATH = 'ruptures/properties.csv'
    INDICES_PATH = 'ruptures/indices.csv'
    FAULTS_PATH = 'ruptures/fault_sections.geojson'
    METADATA_PATH = 'metadata.json'
    LOGIC_TREE_PATH = 'ruptures/logic_tree_branch.json'

    DATAFRAMES = [RATES_PATH, RUPTS_PATH, INDICES_PATH]

    def __init__(self) -> None:
        # self._init_props()
        self._rates = None
        self._ruptures = None
        self._rupture_props = None
        self._indices = None
        self._rs_with_rates = None
        self._fs_with_rates = None
        self._ruptures_with_rates = None
        self._logic_tree_branch: List[Any] = []
        self._fault_regime: str = ''
        self._fault_sections = None
        self._rupture_sections = None
        self._archive_path: Path
        # self._surface_builder: SolutionSurfacesBuilder

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        # write out the `self` dataframes
        if reindex:
            data_to_zip_direct(zip_archive, reindex_dataframe(self._rates).to_csv(), self.RATES_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._ruptures).to_csv(), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._indices).to_csv(), self.INDICES_PATH)
        else:
            data_to_zip_direct(zip_archive, self._rates.to_csv(index=False), self.RATES_PATH)
            data_to_zip_direct(zip_archive, self._ruptures.to_csv(), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, self._indices.to_csv(), self.INDICES_PATH)

    def to_archive(self, archive_path, base_archive_path, compat=True):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
        """
        zout = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)

        # this copies in memory, skipping the datframe files we'll want to overwrite
        zin = zipfile.ZipFile(base_archive_path, 'r')
        for item in zin.infolist():
            if item.filename in self.DATAFRAMES:
                continue
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        """
        Non-compatible mode does not reindex the tables from 0 as required by opensha. So it cannot be
        used to produce opensha reports etc.
        """
        if compat:
            self._write_dataframes(zout, reindex=True)
        else:
            self._write_dataframes(zout, reindex=False)
        self._archive_path = archive_path
        data_to_zip_direct(zout, WARNING, "WARNING.md")

    @property
    def archive_path(self) -> Path:
        return self._archive_path

    def _dataframe_from_csv(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = pd.read_csv(zipfile.Path(self._archive_path, at=path).open())
            # print('prop')
            # print(prop)
            prop = prop.convert_dtypes()
        return prop

    @property
    def logic_tree_branch(self) -> list:
        """
        get values from the opensha logic_tree_branch data file.
        :return: list of value objects
        """
        if not self._logic_tree_branch:
            ltb = json.load(zipfile.Path(self._archive_path, at=self.LOGIC_TREE_PATH).open())
            if type(ltb) == list:
                self._logic_tree_branch = ltb
            elif type(ltb.get('values')) == list:
                self._logic_tree_branch = ltb.get('values')
            else:  # pragma: no cover
                raise ValueError(f"unhandled logic_tree_branch: {ltb}")
        return self._logic_tree_branch

    @property
    def fault_regime(self) -> str:
        """
        get the fault regime as defined in the opensha logic_tree_branch data file.

        :return: "CRUSTAL" or "SUBDUCTION"
        """

        def get_regime() -> str:
            for obj in self.logic_tree_branch:  # .get('values'):
                val = obj.get('value')
                if val:
                    name = val.get('name')
                    if name == 'Fault Regime':
                        return val.get('enumName')
            raise ValueError(
                f"expected Fault Regime missing in solution logic tree, see {self.LOGIC_TREE_PATH}."
            )  # pragma: no cover

        if not self._fault_regime:
            self._fault_regime = get_regime()
        return self._fault_regime

    @property
    def rates(self) -> gpd.GeoDataFrame:
        return self._dataframe_from_csv(self._rates, self.RATES_PATH)

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        return self._dataframe_from_csv(self._ruptures, self.RUPTS_PATH)

    @property
    def indices(self) -> gpd.GeoDataFrame:
        return self._dataframe_from_csv(self._indices, self.INDICES_PATH)

    def set_props(
        self, rates: pd.DataFrame, ruptures: pd.DataFrame, indices: pd.DataFrame, fault_sections: pd.DataFrame
    ):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
