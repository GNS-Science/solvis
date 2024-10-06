import io
import json
import logging
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Optional, Union

import geopandas as gpd
import pandas as pd

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


class InversionSolutionFile:
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
        self._rates = None
        self._ruptures = None
        self._rupture_props = None
        self._indices = None
        self._section_target_slip_rates = None
        self._fast_indices = None
        self._rs_with_rupture_rates = None
        self._fs_with_rates = None
        self._fs_with_soln_rates = None
        self._ruptures_with_rupture_rates: Optional[pd.DataFrame] = None
        self._average_slips = None
        self._logic_tree_branch: List[Any] = []
        self._fault_regime: str = ''
        self._fault_sections: Optional[gpd.GeoDataFrame] = None
        self._rupture_sections = None
        self._archive_path: Optional[Path] = None
        self._archive: Optional[io.BytesIO] = None
        # self._surface_builder: SolutionSurfacesBuilder

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        # write out the `self` dataframes
        log.info("%s write_dataframes with fast_indices: %s" % (type(self), self._fast_indices is not None))
        rates = reindex_dataframe(self._rates) if reindex else self._rates
        rupts = reindex_dataframe(self._ruptures) if reindex else self._ruptures
        indices = reindex_dataframe(self._indices) if reindex else self._indices
        slips = reindex_dataframe(self._average_slips) if reindex else self._average_slips

        data_to_zip_direct(zip_archive, rates.to_csv(index=reindex), self.RATES_PATH)
        data_to_zip_direct(zip_archive, rupts.to_csv(index=reindex), self.RUPTS_PATH)
        data_to_zip_direct(zip_archive, indices.to_csv(index=reindex), self.INDICES_PATH)
        data_to_zip_direct(zip_archive, slips.to_csv(index=reindex), self.AVG_SLIPS_PATH)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolutionFile':
        """
        Read and return an inversion solution file from an OpenSHA archive file or byte-stream.

        Archive validity is checked with the presence of a `ruptures/indices.csv` file.

        Parameters:
            instance_or_path: a Path object, filename or in-memory binary IO stream

        Returns:
            An InversionSolutionFile instance.
        """
        inversion_solution_file = InversionSolutionFile()

        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/indices.csv' in zf.namelist()
            inversion_solution_file._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            inversion_solution_file._archive_path = Path(instance_or_path)

        return inversion_solution_file

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
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
        """Get an in-memory archive instance."""
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

    def _dataframe_from_csv(self, prop, path, dtype=None) -> pd.DataFrame:
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

    def _geodataframe_from_geojson(self, prop, path) -> gpd.GeoDataFrame:
        if not isinstance(prop, gpd.GeoDataFrame):
            prop = gpd.read_file(self.archive.open(path))
        return prop

    @property
    def logic_tree_branch(self) -> list:
        """
        Get values from the opensha `logic_tree_branch` data file.

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
        """
        get the fault regime as defined in the opensha logic_tree_branch data file.

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
    def rupture_rates(self) -> gpd.GeoDataFrame:
        """Get a dataframe containing ruptures and their rates"""
        dtypes: defaultdict = defaultdict(lambda: 'Float32')
        # dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        # dtypes["Annual Rate"] = 'Float32' # pd.Float32Dtype()
        # return pd.read_csv(zipfile.Path(self._archive_path, at=self.RATES_PATH).open(), dtype=dtypes)
        return self._dataframe_from_csv(self._rates, self.RATES_PATH, dtypes)

    @property
    def ruptures(self) -> gpd.GeoDataFrame:
        """Ruptures ruptres."""
        dtypes: defaultdict = defaultdict(lambda: 'Float32')
        # dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'
        return self._dataframe_from_csv(self._ruptures, self.RUPTS_PATH, dtypes)

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

    @property
    def fault_sections(self) -> gpd.GeoDataFrame:
        """
        Get the fault sections and replace slip rates from rupture set with target rates from inverison.
        Cache result.
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
    def rupture_sections(self) -> gpd.GeoDataFrame:
        if self._rupture_sections is not None:
            return self._rupture_sections  # pragma: no cover
        self._rupture_sections = self.build_rupture_sections()
        return self._rupture_sections

    def build_rupture_sections(self) -> gpd.GeoDataFrame:

        tic = time.perf_counter()

        rs = self.indices  # _dataframe_from_csv(self._rupture_sections, 'ruptures/indices.csv').copy()

        # remove "Rupture Index, Num Sections" column
        df_table = rs.drop(rs.iloc[:, :2], axis=1)
        tic0 = time.perf_counter()

        # convert to relational table, turning headings index into plain column
        df2 = df_table.stack().reset_index()

        tic1 = time.perf_counter()
        log.debug('rupture_sections(): time to convert indiced to table: %2.3f seconds' % (tic1 - tic0))

        # remove the headings column
        df2.drop(df2.iloc[:, 1:2], inplace=True, axis=1)
        df2 = df2.set_axis(['rupture', 'section'], axis='columns', copy=False)

        toc = time.perf_counter()
        log.debug('rupture_sections(): time to load and conform rupture_sections: %2.3f seconds' % (toc - tic))
        return df2

    @property
    def rs_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """Get a dataframe joining rupture_sections and rupture_rates."""
        print(self)

        if self._rs_with_rupture_rates is not None:
            return self._rs_with_rupture_rates  # pragma: no cover

        tic = time.perf_counter()
        # df_rupt_rate = self.ruptures.join(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))

        self._rs_with_rupture_rates = self.ruptures_with_rupture_rates.join(
            self.rupture_sections.set_index("rupture"), on=self.ruptures_with_rupture_rates["Rupture Index"]
        )

        toc = time.perf_counter()
        log.info(
            (
                'rs_with_rupture_rates: time to load ruptures_with_rupture_rates '
                'and join with rupture_sections: %2.3f seconds'
            )
            % (toc - tic)
        )
        return self._rs_with_rupture_rates

    @property
    def ruptures_with_rupture_rates(self) -> pd.DataFrame:
        """Get a dataframe joining ruptures and rupture_rates."""
        if self._ruptures_with_rupture_rates is not None:
            return self._ruptures_with_rupture_rates  # pragma: no cover

        tic = time.perf_counter()
        # print(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._ruptures_with_rupture_rates = self.rupture_rates.join(
            self.ruptures.drop(columns="Rupture Index"), on=self.rupture_rates["Rupture Index"]
        )
        if 'key_0' in self._ruptures_with_rupture_rates.columns:
            self._ruptures_with_rupture_rates.drop(columns=['key_0'], inplace=True)
        toc = time.perf_counter()
        log.debug(
            'ruptures_with_rupture_rates(): time to load rates and join with ruptures: %2.3f seconds' % (toc - tic)
        )
        return self._ruptures_with_rupture_rates

    @property
    def fault_sections_with_solution_slip_rates(self) -> gpd.GeoDataFrame:
        """Calculate and cache fault sections and their solution slip rates.

        NB: Solution slip rate combines input (avg slips) and solution (rupture rates).
        """
        if self._fs_with_soln_rates is not None:
            return self._fs_with_soln_rates

        tic = time.perf_counter()
        self._fs_with_soln_rates = self._get_soln_rates()
        toc = time.perf_counter()
        log.debug('fault_sections_with_solution_rates: time to calculate solution rates: %2.3f seconds' % (toc - tic))
        return self._fs_with_soln_rates

    def _get_soln_rates(self):

        average_slips = self.average_slips
        # for every subsection, find the ruptures on it
        fault_sections_wr = self.fault_sections.copy()
        for ind, fault_section in self.fault_sections.iterrows():
            fault_id = fault_section['FaultID']
            fswr_gt0 = self.fault_sections_with_rupture_rates[
                (self.fault_sections_with_rupture_rates['FaultID'] == fault_id)
                & (self.fault_sections_with_rupture_rates['Annual Rate'] > 0.0)
            ]
            fault_sections_wr.loc[ind, 'Solution Slip Rate'] = sum(
                fswr_gt0['Annual Rate'] * average_slips.loc[fswr_gt0['Rupture Index']]['Average Slip (m)']
            )

        return fault_sections_wr

    @property
    def fault_sections_with_rupture_rates(self) -> gpd.GeoDataFrame:
        """
        Calculate and cache the fault sections and their rupture rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._fs_with_rates is not None:
            return self._fs_with_rates

        tic = time.perf_counter()
        self._fs_with_rates = self.rs_with_rupture_rates.join(self.fault_sections, 'section', how='inner')
        toc = time.perf_counter()
        log.debug(
            (
                'fault_sections_with_rupture_rates: time to load rs_with_rupture_rates '
                'and join with fault_sections: %2.3f seconds'
            )
            % (toc - tic)
        )

        # self._fs_with_rates = self.fault_sections.join(self.ruptures_with_rupture_rates,
        #     on=self.fault_sections["Rupture Index"] )
        return self._fs_with_rates

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
