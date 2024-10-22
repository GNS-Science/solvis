"""
An InversionSolution Archive file helper.

This module handles files having the OpenSHA InversionSolution archive format.

It provides conversions from the original file formats to pandas dataframe instances
with caching and some error handling.
"""
import io
import json
import logging
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, cast

import geopandas as gpd
import pandas as pd

from .typing import InversionSolutionProtocol

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from .dataframe_models import RuptureRateSchema, RuptureSchema

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
using the Solvis Python library.

Data may have been filtered out of an original
Inversion Solution archive file:
 - 'solution/rates.csv'
 - 'ruptures/properties.csv'
 - 'ruptures/indices.csv'
 - 'ruptures/average_slips.csv'

"""
"A warning added to archives that have been modified by Solvis."


def reindex_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    new_df = dataframe.copy().reset_index(drop=True).drop(columns=['Rupture Index'])  # , errors='ignore')
    new_df.index = new_df.index.rename('Rupture Index')
    # print("NEW DF", new_df)
    return new_df

#InversionSolutionProtocol
class InversionSolutionFile():
    """
    Class to handle the OpenSHA modular archive file form.

    Methods:
        to_archive: serialise an instance to a zip archive.
        filter_solution: get a new InversionSolution instance, filtered by rupture ids.
        set_props:

    Attributes:
        archive: the archive instance.
        archive_path: the archive path name.
        ruptures: get the solution ruptures dataframe.
        fault_regime:
        indices:
        logic_tree_branch:
        rupture_rates:
        ruptures:
        section_target_slip_rates:
    """

    RATES_PATH = 'solution/rates.csv'
    RUPTS_PATH = 'ruptures/properties.csv'
    INDICES_PATH = 'ruptures/indices.csv'
    AVG_SLIPS_PATH = 'ruptures/average_slips.csv'
    FAULTS_PATH = 'ruptures/fault_sections.geojson'
    METADATA_PATH = 'metadata.json'
    LOGIC_TREE_PATH = 'ruptures/logic_tree_branch.json'
    SECT_SLIP_RATES_PATH = 'ruptures/sect_slip_rates.csv'

    DATAFRAMES = [RATES_PATH, RUPTS_PATH, INDICES_PATH, AVG_SLIPS_PATH]

    def __init__(self) -> None:
        # self._init_props()
        self._rates: Optional[pd.DataFrame] = None
        self._ruptures: Optional[pd.DataFrame] = None
        self._rupture_props = None
        self._indices: Optional[pd.DataFrame] = None
        self._section_target_slip_rates = None
        # self._fast_indices = None
        ## self._rs_with_rupture_rates: Optional[pd.DataFrame] = None
        self._fs_with_rates: Optional[pd.DataFrame] = None
        self._fs_with_soln_rates: Optional[pd.DataFrame] = None
        ## self._ruptures_with_rupture_rates: Optional[pd.DataFrame] = None
        self._average_slips: Optional[pd.DataFrame] = None
        self._logic_tree_branch: List[Any] = []
        self._fault_regime: str = ''
        self._fault_sections: Optional[pd.DataFrame] = None
        self._rupture_sections: Optional[gpd.GeoDataFrame] = None
        self._archive_path: Optional[Path] = None
        self._archive: Optional[io.BytesIO] = None
        # self._surface_builder: SolutionSurfacesBuilder

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        # write out the `self` dataframes
        # log.info("%s write_dataframes with fast_indices: %s" % (type(self), self._fast_indices is not None))
        rates = reindex_dataframe(self.rupture_rates) if reindex else self.rupture_rates
        rupts = reindex_dataframe(self.ruptures) if reindex else self.ruptures
        indices = reindex_dataframe(self.indices) if reindex else self.indices
        slips = reindex_dataframe(self.average_slips) if reindex else self.average_slips

        data_to_zip_direct(zip_archive, rates.to_csv(index=reindex), self.RATES_PATH)
        data_to_zip_direct(zip_archive, rupts.to_csv(index=reindex), self.RUPTS_PATH)
        data_to_zip_direct(zip_archive, indices.to_csv(index=reindex), self.INDICES_PATH)
        data_to_zip_direct(zip_archive, slips.to_csv(index=reindex), self.AVG_SLIPS_PATH)

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        """Write the current solution to a new zip archive.

        Optionally cloning data from a base archive.

        In non-compatible mode (the default) rupture ids may not be a contiguous, 0-based sequence,
        so the archive will not be suitable for use with opensha. Compatible mode will reindex rupture tables,
        so that the original rutpure ids are lost.

        Args:
            archive_path: path to write to.
            base_archive_path: path to an InversionSolution archive to clone data from.
            compat: if True reindex the dataframes so that the archive remains compatible with opensha.
        """
        if base_archive_path is None:
            # try to use this archive, rather than a base archive
            zin = self._archive
        else:
            zin = zipfile.ZipFile(base_archive_path, 'r')

        log.debug('create zipfile %s with method %s' % (archive_path, ZIP_METHOD))
        zout = zipfile.ZipFile(archive_path, 'w', ZIP_METHOD)

        log.debug('to_archive: skipping files: %s' % self.DATAFRAMES)
        # this copies in memory, skipping the dataframe files we'll want to overwrite

        for item in zin.infolist():
            if item.filename in self.DATAFRAMES:
                continue
            log.debug("writing to zipfile: %s" % item.filename)
            buffer = zin.read(item.filename)
            zout.writestr(item, buffer)

        """

        """
        if compat:
            self._write_dataframes(zout, reindex=True)
        else:
            self._write_dataframes(zout, reindex=False)
        self._archive_path = archive_path
        data_to_zip_direct(zout, WARNING, "WARNING.md")

    @property
    def archive_path(self) -> Optional[Path]:
        """The path of the archive (if any).

        Returns:
            filepath: the file system path.
        """
        return self._archive_path

    @property
    def archive(self) -> zipfile.ZipFile:
        """An in-memory archive instance."""
        log.debug('archive path: %s archive: %s ' % (self._archive_path, self._archive))
        archive = None
        if self._archive is None:
            if self._archive_path is None:
                raise RuntimeError("archive_path ARGG")
            else:
                tic = time.perf_counter()
                data = io.BytesIO(open(self._archive_path, 'rb').read())
                archive = zipfile.ZipFile(data)
                toc = time.perf_counter()
                log.debug('archive time to open zipfile %s %2.3f seconds' % (self._archive_path, toc - tic))
        else:
            archive = zipfile.ZipFile(self._archive)
        return archive

    def _dataframe_from_csv(self, prop, path, dtype=None):
        log.debug('_dataframe_from_csv( %s, %s, %s )' % (prop, path, dtype))
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


    def _geodataframe_from_geojson(self, prop, path):
        if not isinstance(prop, pd.DataFrame):
            prop = gpd.read_file(self.archive.open(path))
        return prop

    @property
    def fault_sections(self) -> 'DataFrame[FaultSectionSchema]':
        """
        Get the fault sections and replace slip rates from rupture set with target rates from inverison.
        Cache result.

        Returns:
            pd.DataFrame: participation rates dataframe
        """
        if self._fault_sections is not None:
            return self._fault_sections

        tic = time.perf_counter()
        self._fault_sections = self._geodataframe_from_geojson(self._fault_sections, self.FAULTS_PATH)
        self._fault_sections = self._fault_sections.join(self.section_target_slip_rates)
        self._fault_sections.drop(columns=["SlipRate", "SlipRateStdDev", "Section Index"], inplace=True)
        mapper = {
            "Slip Rate (m/yr)": "Target Slip Rate",
            "Slip Rate Standard Deviation (m/yr)": "Target Slip Rate StdDev",
        }
        self._fault_sections.rename(columns=mapper, inplace=True)
        toc = time.perf_counter()
        log.debug('fault_sections: time to load fault_sections: %2.3f seconds' % (toc - tic))
        return self._fault_sections

    @property
    def logic_tree_branch(self) -> list:
        """Values from the opensha `logic_tree_branch` data file.

        Returns:
            list of value objects
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
        """The fault regime as defined in the opensha logic_tree_branch data file.

        Returns:
            `CRUSTAL` or `SUBDUCTION` respectively.
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
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        dtypes: defaultdict = defaultdict(lambda: 'Float32')
        # dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        # dtypes["Annual Rate"] = 'Float32' # pd.Float32Dtype()
        # return pd.read_csv(zipfile.Path(self._archive_path, at=self.RATES_PATH).open(), dtype=dtypes)
        df = self._dataframe_from_csv(self._rates, self.RATES_PATH, dtypes)
        return cast('DataFrame[RuptureRateSchema]', df)

    @property
    def ruptures(self) -> 'DataFrame[RuptureSchema]':
        dtypes: defaultdict = defaultdict(lambda: 'Float32')
        # dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'
        df = self._dataframe_from_csv(self._ruptures, self.RUPTS_PATH, dtypes)
        return cast('DataFrame[RuptureSchema]', df)

    @property
    def indices(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(lambda: 'Int32')
        return self._dataframe_from_csv(self._indices, self.INDICES_PATH, dtypes)

    @property
    def average_slips(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(np.float64)
        dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'
        return self._dataframe_from_csv(self._average_slips, self.AVG_SLIPS_PATH)  # , dtypes)

    @property
    def section_target_slip_rates(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(np.float32)
        dtypes = {}
        dtypes["Section Index"] = 'UInt32'
        return self._dataframe_from_csv(self._section_target_slip_rates, self.SECT_SLIP_RATES_PATH)

    def set_props(
        self,
        rates: pd.DataFrame,
        ruptures: pd.DataFrame,
        indices: pd.DataFrame,
        fault_sections: pd.DataFrame,
        average_slips: pd.DataFrame,
    ):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._average_slips = average_slips
