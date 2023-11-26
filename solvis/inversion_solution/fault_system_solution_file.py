import logging
import zipfile
from collections import defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd

from .inversion_solution_file import InversionSolutionFile, data_to_zip_direct, reindex_dataframe

log = logging.getLogger(__name__)

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


class FaultSystemSolutionFile(InversionSolutionFile):
    """
    Class to handle the NZHSM Compositie solution modular archive file form
    """

    _composite_rates: pd.DataFrame = ...
    _aggregate_rates: pd.DataFrame = ...

    COMPOSITE_RATES_PATH = 'composite_rates.csv'
    AGGREGATE_RATES_PATH = 'aggregate_rates.csv'

    FAST_INDICES_PATH = 'ruptures/fast_indices.csv'  # store indices in standard table format for much faster I/O

    DATAFRAMES = [
        # InversionSolutionFile.RATES_PATH,
        InversionSolutionFile.RUPTS_PATH,
        InversionSolutionFile.INDICES_PATH,
        COMPOSITE_RATES_PATH,
        AGGREGATE_RATES_PATH,
        FAST_INDICES_PATH,
    ]

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):

        log.info("%s write_dataframes with fast_indices: %s" % (type(self), self._fast_indices is not None))

        if reindex:
            data_to_zip_direct(
                zip_archive, reindex_dataframe(self._composite_rates).to_csv(index=True), self.COMPOSITE_RATES_PATH
            )
            data_to_zip_direct(
                zip_archive, reindex_dataframe(self._aggregate_rates).to_csv(index=True), self.AGGREGATE_RATES_PATH
            )
            # data_to_zip_direct(zip_archive, reindex_dataframe(self._rates).to_csv(), self.RATES_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._ruptures).to_csv(index=False), self.RUPTS_PATH)
            if self._fast_indices is not None:
                data_to_zip_direct(
                    zip_archive, reindex_dataframe(self._fast_indices).to_csv(index=False), self.FAST_INDICES_PATH
                )
            else:
                data_to_zip_direct(zip_archive, reindex_dataframe(self._indices).to_csv(index=False), self.INDICES_PATH)

        else:
            data_to_zip_direct(zip_archive, self._composite_rates.to_csv(index=False), self.COMPOSITE_RATES_PATH)
            # data_to_zip_direct(zip_archive, self._rates.to_csv(index=False), self.RATES_PATH)
            data_to_zip_direct(zip_archive, self._aggregate_rates.to_csv(index=False), self.AGGREGATE_RATES_PATH)
            data_to_zip_direct(zip_archive, self._ruptures.to_csv(index=False), self.RUPTS_PATH)
            if self._fast_indices is not None:
                data_to_zip_direct(zip_archive, self._fast_indices.to_csv(index=False), self.FAST_INDICES_PATH)
            else:
                data_to_zip_direct(zip_archive, self._indices.to_csv(index=False), self.INDICES_PATH)

    def to_archive(self, archive_path, base_archive_path, compat=False):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
        """
        log.debug("%s to_archive %s" % (type(self), archive_path))
        self.enable_fast_indices()
        super().to_archive(archive_path, base_archive_path, compat=False)

    @property
    def composite_rates(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(np.float32)
        dtypes = {}

        dtypes["Rupture Index"] = pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        df = self._dataframe_from_csv(self._composite_rates, self.COMPOSITE_RATES_PATH, dtypes)
        return df.set_index(["solution_id", "Rupture Index"], drop=False)

    @property
    def rates(self) -> gpd.GeoDataFrame:
        return self.aggregate_rates

    @property
    def aggregate_rates(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(np.float32)
        dtypes["Rupture Index"] = pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        df = self._dataframe_from_csv(self._aggregate_rates, self.AGGREGATE_RATES_PATH, dtypes)
        return df.set_index(["fault_system", "Rupture Index"], drop=False)

    # @property
    # def rates(self):
    #     raise NotImplementedError("Use aggregate_rates instead")

    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(pd.UInt32Dtype)
        dtypes["ruptures"] = pd.UInt32Dtype()
        dtypes["sections"] = pd.UInt32Dtype()
        return self._dataframe_from_csv(self._fast_indices, self.FAST_INDICES_PATH)  # , dtypes)
