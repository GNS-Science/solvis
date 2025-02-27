"""
An InversionSolution archive file helper.

Supports files in OpenSHA InversionSolution archive format.

It provides conversions from the original file formats to pandas dataframe instances
with caching and some error handling.
"""

import io
import json
import logging
import time
import zipfile
from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Union, cast

import geopandas as gpd
import pandas as pd

from solvis.dochelper import inherit_docstrings

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from ..dataframe_models import FaultSectionSchema, RuptureRateSchema, RuptureSchema

log = logging.getLogger(__name__)

ZIP_METHOD = zipfile.ZIP_STORED

WARNING = """
# Attention

This Inversion Solution archive has been modified
using the Solvis Python library.

Data may have been filtered out of an original
Inversion Solution archive file:
 - 'solution/rates.csv'
 - 'ruptures/properties.csv'
 - 'ruptures/indices.csv'
 - 'ruptures/average_slips.csv'

"""  # warning added to archives that have been modified by Solvis.


def data_to_zip_direct(z, data, name):
    log.debug('data_to_zip_direct %s' % name)
    zinfo = zipfile.ZipInfo(name, time.localtime()[:6])
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zinfo, data)


def reindex_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    new_df = dataframe.copy().reset_index(drop=True).drop(columns=['Rupture Index'])  # , errors='ignore')
    new_df.index = new_df.index.rename('Rupture Index')
    # print("NEW DF", new_df)
    return new_df


@inherit_docstrings
class InversionSolutionFile:
    """
    Class to handle the OpenSHA modular archive file form.

    Methods:
        to_archive: serialise an instance to a zip archive.
    """

    RATES_PATH = 'solution/rates.csv'
    """description of RATES_PATH
    """
    RUPTS_PATH = 'ruptures/properties.csv'
    INDICES_PATH = 'ruptures/indices.csv'
    AVG_SLIPS_PATH = 'ruptures/average_slips.csv'
    FAULTS_PATH = 'ruptures/fault_sections.geojson'
    METADATA_PATH = 'metadata.json'
    LOGIC_TREE_PATH = 'ruptures/logic_tree_branch.json'
    SECT_SLIP_RATES_PATH = 'ruptures/sect_slip_rates.csv'

    DATAFRAMES = [RATES_PATH, RUPTS_PATH, INDICES_PATH, AVG_SLIPS_PATH]

    def __init__(self) -> None:
        """Initializes the InversionSolutionFile object."""
        self._rates: Optional[pd.DataFrame] = None
        self._ruptures: Optional[pd.DataFrame] = None
        self._indices: Optional[pd.DataFrame] = None
        self._section_target_slip_rates: Optional[pd.DataFrame] = None
        self._average_slips: Optional[pd.DataFrame] = None
        self._archive_path: Optional[Path] = None
        self._archive: Optional[io.BytesIO] = None

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        """
        Writes the dataframes to a zip archive.

        :param zip_archive: The zip archive to write to.
        :param reindex: Whether or not to reindex the dataframes before writing them.
        """
        rates = reindex_dataframe(self.rupture_rates) if reindex else self.rupture_rates
        rupts = reindex_dataframe(self.ruptures) if reindex else self.ruptures
        indices = reindex_dataframe(self.indices) if reindex else self.indices
        slips = reindex_dataframe(self.average_slips) if reindex else self.average_slips

        data_to_zip_direct(zip_archive, rates.to_csv(index=reindex), self.RATES_PATH)
        data_to_zip_direct(zip_archive, rupts.to_csv(index=reindex), self.RUPTS_PATH)
        data_to_zip_direct(zip_archive, indices.to_csv(index=reindex), self.INDICES_PATH)
        data_to_zip_direct(zip_archive, slips.to_csv(index=reindex), self.AVG_SLIPS_PATH)

    def to_archive(self, archive_path_or_buffer: Union[Path, str, io.BytesIO], base_archive_path=None, compat=False):
        """Write the current solution file to a new zip archive.

        Optionally cloning data from a base archive.

        In non-compatible mode (the default) rupture ids may not be a contiguous, 0-based sequence,
        so the archive will not be suitable for use with opensha. Compatible mode will reindex rupture tables,
        so that the original rutpure ids are lost.

        Args:
            archive_path_or_buffer: path or buffrer to write.
            base_archive_path: path to an InversionSolution archive to clone data from.
            compat: if True reindex the dataframes so that the archive remains compatible with opensha.
        """
        if base_archive_path is None:
            # try to use this archive, rather than a base archive
            zin = self.archive
        else:
            zin = zipfile.ZipFile(base_archive_path, 'r')

        log.debug('create zipfile %s with method %s' % (archive_path_or_buffer, ZIP_METHOD))
        zout = zipfile.ZipFile(archive_path_or_buffer, 'w', ZIP_METHOD)

        log.debug('to_archive: skipping files: %s' % self.DATAFRAMES)
        # this copies in memory, skipping the dataframe files we'll want to overwrite
        for item in zin.infolist():
            if item.filename in self.DATAFRAMES:
                continue
            log.debug("writing to zipfile: %s" % item.filename)
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        if compat:
            self._write_dataframes(zout, reindex=True)
        else:
            self._write_dataframes(zout, reindex=False)

        data_to_zip_direct(zout, WARNING, "WARNING.md")

        if isinstance(archive_path_or_buffer, io.BytesIO):
            self._archive = archive_path_or_buffer
        else:
            self._archive_path = cast(Path, archive_path_or_buffer)

    @property
    def archive_path(self) -> Optional[Path]:
        """
        Get the path to the current archive file.

        Returns:
            The path to the archive file, or None if the archive is in a buffer.
        """
        return self._archive_path

    @property
    def archive(self) -> zipfile.ZipFile:
        """
        Open and cache the zip archive.

        This property opens the zip archive from the specified path or buffer,
        caches it in memory for efficient access, and returns a `zipfile.ZipFile`
        object. If the archive is already cached, it simply returns the cached
        version.

        Returns:
            A `zipfile.ZipFile` object representing the open archive.
        """
        log.debug('archive path: %s archive: %s ' % (self._archive_path, self._archive))
        if self._archive is None:
            if self._archive_path is None:  # pragma: no cover  (this should never happen)
                raise RuntimeError("archive_path cannot be None, unless we have an in-memory archive")
            else:
                tic = time.perf_counter()
                self._archive = io.BytesIO(open(self._archive_path, 'rb').read())
                toc = time.perf_counter()
                log.debug('archive time to open zipfile %s %2.3f seconds' % (self._archive_path, toc - tic))

        return zipfile.ZipFile(self._archive)

    def _dataframe_from_csv(self, path, dtype=None):
        """
        Load a dataframe from a CSV file in the archive.

        Args:
            path: The path to the CSV file within the archive.
            dtype: A dictionary specifying data types for specific columns (optional).

        Returns:
            The loaded dataframe.
        """
        log.debug('_dataframe_from_csv( %s, %s )' % (path, dtype))

        tic = time.perf_counter()
        data = self.archive.open(path)
        toc = time.perf_counter()
        log.debug('dataframe_from_csv() time to open datafile %s %2.3f seconds' % (path, toc - tic))
        tic = time.perf_counter()
        df0 = pd.read_csv(data, dtype=dtype)
        toc = time.perf_counter()
        log.debug('dataframe_from_csv() time to load dataframe %s %2.3f seconds' % (path, toc - tic))
        return df0

    @property
    @cache
    def fault_sections(self) -> 'DataFrame[FaultSectionSchema]':
        """
        Get the fault sections with target slip rates.

        Returns:
            A DataFrame containing fault section data with target slip rates.
        """
        tic = time.perf_counter()
        fault_sections = gpd.read_file(self.archive.open(self.FAULTS_PATH))
        fault_sections = fault_sections.join(self.section_target_slip_rates)
        fault_sections.drop(columns=["SlipRate", "SlipRateStdDev", "Section Index"], inplace=True)
        mapper = {
            "Slip Rate (m/yr)": "Target Slip Rate",
            "Slip Rate Standard Deviation (m/yr)": "Target Slip Rate StdDev",
        }
        fault_sections.rename(columns=mapper, inplace=True)
        toc = time.perf_counter()
        log.debug('fault_sections: time to load fault_sections: %2.3f seconds' % (toc - tic))
        return cast('DataFrame[FaultSectionSchema]', fault_sections)

    @property
    @cache
    def logic_tree_branch(self) -> List[Any]:
        """
        Get the logic tree branches from the archive.

        Returns:
            A list of logic tree branch data.
        """
        ltb = json.load(self.archive.open(self.LOGIC_TREE_PATH))
        if isinstance(ltb, list):
            logic_tree_branch = ltb
        elif isinstance(ltb.get('values'), list):
            logic_tree_branch = ltb.get('values')
        else:  # pragma: no cover
            raise ValueError(f"unhandled logic_tree_branch: {ltb}")
        return logic_tree_branch

    @property
    @cache
    def fault_regime(self) -> str:
        """
        Get the fault regime from the logic tree branches.

        Returns:
            The fault regime name as a string `CRUSTAL` or `SUBDUCTION` respectively.
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

        return get_regime()

    @property
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        """
        Get the rupture rates from the archive.

        Returns:
            A DataFrame containing rupture rate data.
        """
        if self._rates is None:
            dtypes: defaultdict = defaultdict(lambda: 'Float32')
            dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
            dtypes["fault_system"] = pd.CategoricalDtype()
            self._rates = self._dataframe_from_csv(self.RATES_PATH, dtypes)
        return cast('DataFrame[RuptureRateSchema]', self._rates)

    @property
    @cache
    def ruptures(self) -> 'DataFrame[RuptureSchema]':
        """
        Get the ruptures from the archive.

        Returns:
            A DataFrame containing rupture data.
        """
        if self._ruptures is None:
            dtypes: defaultdict = defaultdict(lambda: 'Float32')
            dtypes["Rupture Index"] = 'UInt32'
            self._ruptures = self._dataframe_from_csv(self.RUPTS_PATH, dtypes)
        return cast('DataFrame[RuptureSchema]', self._ruptures)

    @property
    @cache
    def indices(self) -> gpd.GeoDataFrame:
        """
        Get the rupture indices from the archive.

        Returns:
            A GeoDataFrame containing rupture index data.
        """
        if self._indices is None:
            dtypes: defaultdict = defaultdict(lambda: 'Int32')
            self._indices = self._dataframe_from_csv(self.INDICES_PATH, dtypes)
        return self._indices

    @property
    @cache
    def average_slips(self) -> gpd.GeoDataFrame:
        """
        Get the average slips from the archive.

        Returns:
            A GeoDataFrame containing average slip data.
        """
        # dtypes: defaultdict = defaultdict(np.float64)
        if self._average_slips is None:
            dtypes = {}
            dtypes["Rupture Index"] = 'UInt32'
            self._average_slips = self._dataframe_from_csv(self.AVG_SLIPS_PATH, dtypes)
        return self._average_slips

    @property
    def section_target_slip_rates(self) -> gpd.GeoDataFrame:
        """
        Get the section target slip rates from the archive.

        Returns:
            A GeoDataFrame containing section target slip rate data.
        """
        # dtypes: defaultdict = defaultdict(np.float32)
        if self._section_target_slip_rates is None:
            dtypes = {}
            dtypes["Section Index"] = 'UInt32'
            self._section_target_slip_rates = self._dataframe_from_csv(self.SECT_SLIP_RATES_PATH, dtypes)
        return self._section_target_slip_rates

    def set_props(
        self,
        rates: pd.DataFrame,
        ruptures: pd.DataFrame,
        indices: pd.DataFrame,
        fault_sections: pd.DataFrame,
        average_slips: pd.DataFrame,
    ):
        """
        Set the properties for this object.

        Args:
            rates: A DataFrame containing rupture rate data.
            ruptures: A DataFrame containing rupture data.
            indices: A DataFrame containing rupture index data.
            fault_sections: A DataFrame containing fault section data with target slip rates.
            average_slips: A GeoDataFrame containing average slip data.
        """
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._average_slips = average_slips
