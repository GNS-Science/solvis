import logging
import zipfile
from collections import defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd

from .inversion_solution_file import InversionSolutionFile, data_to_zip_direct

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
        InversionSolutionFile.RATES_PATH,
        InversionSolutionFile.RUPTS_PATH,
        InversionSolutionFile.INDICES_PATH,
        COMPOSITE_RATES_PATH,
        AGGREGATE_RATES_PATH,
        FAST_INDICES_PATH,
    ]

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        data_to_zip_direct(zip_archive, self._composite_rates.to_csv(index=reindex), self.COMPOSITE_RATES_PATH)
        data_to_zip_direct(zip_archive, self._aggregate_rates.to_csv(index=reindex), self.AGGREGATE_RATES_PATH)
        if self._fast_indices is not None:
            data_to_zip_direct(zip_archive, self._fast_indices.to_csv(index=reindex), self.FAST_INDICES_PATH)

        super()._write_dataframes(zip_archive, reindex)

    def to_archive(self, archive_path, base_archive_path, compat=False):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
        """
        log.debug("%s to_archive %s" % (type(self), archive_path))

        # Now we need a rates table, structurecd correctly, with weights from the aggregate_rates
        rates = self.aggregate_rates.drop(columns=['rate_max', 'rate_min', 'rate_count', 'fault_system']).rename(
            columns={"rate_weighted_mean": "Annual Rate"}
        )
        self._rates = rates

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
    def rupture_rates(self) -> gpd.GeoDataFrame:
        return self.aggregate_rates

    @property
    def aggregate_rates(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(np.float32)
        dtypes["Rupture Index"] = pd.UInt32Dtype()
        dtypes["fault_system"] = pd.CategoricalDtype()
        df = self._dataframe_from_csv(self._aggregate_rates, self.AGGREGATE_RATES_PATH, dtypes)
        return df.set_index(["fault_system", "Rupture Index"], drop=False)

    # @property
    # def rupture_rates(self):
    #     raise NotImplementedError("Use aggregate_rates instead")

    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        dtypes: defaultdict = defaultdict(pd.UInt32Dtype)
        dtypes["ruptures"] = pd.UInt32Dtype()
        dtypes["sections"] = pd.UInt32Dtype()
        return self._dataframe_from_csv(self._fast_indices, self.FAST_INDICES_PATH)  # , dtypes)
