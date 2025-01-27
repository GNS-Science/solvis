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
from typing import TYPE_CHECKING, Any, List, Optional, Union, cast

import geopandas as gpd
import pandas as pd

from ..typing import InversionSolutionFileProtocol

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from .dataframe_models import FaultSectionSchema, RuptureRateSchema, RuptureSchema

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


class InversionSolutionFile(InversionSolutionFileProtocol):
    """
    Class to handle the OpenSHA modular archive file form.

    Methods:
        to_archive: serialise an instance to a zip archive.
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

    def to_archive(self, archive_path_or_buffer: Union[Path, str, io.BytesIO], base_archive_path=None, compat=False):
        """Write the current solution file to a new zip archive.

        Optionally cloning data from a base archive.

        In non-compatible mode (the default) rupture ids may not be a contiguous, 0-based sequence,
        so the archive will not be suitable for use with opensha. Compatible mode will reindex rupture tables,
        so that the original rutpure ids are lost.

        Args:
            archive_path: path or buffrer to write.
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
        return self._archive_path

    @property
    def archive(self) -> zipfile.ZipFile:
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

    @property
    def fault_sections(self) -> 'DataFrame[FaultSectionSchema]':
        if self._fault_sections is not None:
            return cast('DataFrame[FaultSectionSchema]', self._fault_sections)

        tic = time.perf_counter()
        self._fault_sections = gpd.read_file(self.archive.open(self.FAULTS_PATH))
        self._fault_sections = self._fault_sections.join(self.section_target_slip_rates)
        self._fault_sections.drop(columns=["SlipRate", "SlipRateStdDev", "Section Index"], inplace=True)
        mapper = {
            "Slip Rate (m/yr)": "Target Slip Rate",
            "Slip Rate Standard Deviation (m/yr)": "Target Slip Rate StdDev",
        }
        self._fault_sections.rename(columns=mapper, inplace=True)
        toc = time.perf_counter()
        log.debug('fault_sections: time to load fault_sections: %2.3f seconds' % (toc - tic))
        return cast('DataFrame[FaultSectionSchema]', self._fault_sections)

    @property
    def logic_tree_branch(self) -> list:
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
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._average_slips = average_slips
