import json
import logging
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Optional

import geopandas as gpd
import numpy as np
import pandas as pd

from .typing import InversionSolutionProtocol

log = logging.getLogger(__name__)

# from functools import cached_property

"""
zipfile.ZIP_STORED

    The numeric constant for an uncompressed archive member.

zipfile.ZIP_DEFLATED

    The numeric constant for the usual ZIP compression method. This requires the zlib module.

zipfile.ZIP_BZIP2

    The numeric constant for the BZIP2 compression method. This requires the bz2 module.

    New in version 3.3.

zipfile.ZIP_LZMA

    The numeric constant for the LZMA compression method. This requires the lzma module.
"""

ZIP_METHOD = zipfile.ZIP_STORED


def data_to_zip_direct(z, data, name):
    log.debug('data_to_zip_direct %s' % name)
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
        self._fast_indices = None
        self._fast_indices = None
        self._rs_with_rates = None
        self._fs_with_rates = None
        self._ruptures_with_rates = None
        self._logic_tree_branch: List[Any] = []
        self._fault_regime: str = ''
        self._fault_sections = None
        self._rupture_sections = None
        self._archive_path: Optional[Path] = None
        self._archive: Optional[zipfile.ZipFile] = None
        # self._surface_builder: SolutionSurfacesBuilder

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        # write out the `self` dataframes
        log.info("%s write_dataframes with fast_indices: %s" % (type(self), self._fast_indices is not None))

        if reindex:  # for compatible
            data_to_zip_direct(zip_archive, reindex_dataframe(self._rates).to_csv(index=True), self.RATES_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._ruptures).to_csv(index=True), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._indices).to_csv(index=True), self.INDICES_PATH)
        else:
            data_to_zip_direct(zip_archive, self._rates.to_csv(index=False), self.RATES_PATH)
            data_to_zip_direct(zip_archive, self._ruptures.to_csv(index=False), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, self._indices.to_csv(index=False), self.INDICES_PATH)

    def to_archive(self, archive_path, base_archive_path, compat=False):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
        """
        log.debug('create zipfile %s with method %s' % (archive_path, ZIP_METHOD))
        zout = zipfile.ZipFile(archive_path, 'w', ZIP_METHOD)

        # this copies in memory, skipping the dataframe files we'll want to overwrite
        zin = zipfile.ZipFile(base_archive_path, 'r')

        log.debug('to_archive: skipping files: %s' % self.DATAFRAMES)
        for item in zin.infolist():
            if item.filename in self.DATAFRAMES:
                continue
            log.debug("writing to zipfile: %s" % item.filename)
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
    def archive_path(self) -> Optional[Path]:
        return self._archive_path

    @property
    def archive(self) -> zipfile.ZipFile:
        log.debug('archive path: %s archive: %s ' % (self._archive_path, self._archive))
        if self._archive is None:
            if self._archive_path is None:
                raise RuntimeError("archive_path ARGG")
            else:
                tic = time.perf_counter()
                self._archive = zipfile.ZipFile(self._archive_path)
                toc = time.perf_counter()
                log.debug('archive time to open zipfile %s %2.3f seconds' % (self._archive_path, toc - tic))
        return self._archive

    def _dataframe_from_csv(self, prop, path, dtype={}):
        if not isinstance(prop, pd.DataFrame):
            tic = time.perf_counter()
            data = self.archive.open(path)
            toc = time.perf_counter()
            log.debug('dataframe_from_csv() time to open datafile %s %2.3f seconds' % (path, toc - tic))
            tic = time.perf_counter()
            prop = pd.read_csv(data, dtype=dtype)
            toc = time.perf_counter()
            log.debug('dataframe_from_csv() time to load dataframe %s %2.3f seconds' % (path, toc - tic))
        return prop

    @property
    def logic_tree_branch(self) -> list:
        """
        get values from the opensha logic_tree_branch data file.
        :return: list of value objects
        """
        if not self._logic_tree_branch:
            ltb = json.load(self.archive.open(self.LOGIC_TREE_PATH))
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
        dtypes: defaultdict = defaultdict(np.float32)
        dtypes["Rupture Index"] = pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        # return pd.read_csv(zipfile.Path(self._archive_path, at=self.RATES_PATH).open(), dtype=dtypes)
        return self._dataframe_from_csv(self._rates, self.RATES_PATH, dtypes)

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(np.float32)
        dtypes["Rupture Index"] = pd.UInt32Dtype()
        return self._dataframe_from_csv(self._ruptures, self.RUPTS_PATH, dtypes)

    @property
    def indices(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(pd.UInt16Dtype)
        # dtypes["Rupture Index"] = pd.UInt32Dtype()
        # dtypes["Num Sections"] = pd.UInt16Dtype()
        return self._dataframe_from_csv(self._indices, self.INDICES_PATH)  # no dtype is faster!!

    def set_props(
        self, rates: pd.DataFrame, ruptures: pd.DataFrame, indices: pd.DataFrame, fault_sections: pd.DataFrame
    ):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
