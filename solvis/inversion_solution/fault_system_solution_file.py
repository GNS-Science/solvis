import logging
import zipfile
from typing import TYPE_CHECKING, Optional

import geopandas as gpd
import pandas as pd

from .inversion_solution_file import InversionSolutionFile, data_to_zip_direct

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from .dataframe_models import RuptureRateSchema

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
    Class to handle the solution modular archive file form
    """

    _composite_rates: Optional[pd.DataFrame] = None
    _aggregate_rates: Optional[pd.DataFrame] = None
    _fast_indices: Optional[pd.DataFrame] = None

    COMPOSITE_RATES_PATH = 'composite_rates.csv'
    AGGREGATE_RATES_PATH = 'aggregate_rates.csv'

    FAST_INDICES_PATH = 'ruptures/fast_indices.csv'  # store indices in standard table format for much faster I/O

    # OPENSHA_ONLY
    # OPENSHA_LTB_PATH = 'ruptures/logic_tree_branch.json'
    OPENSHA_SECT_POLYS_PATH = 'ruptures/sect_polygons.geojson'
    OPENSHA_GRID_REGION_PATH = 'ruptures/grid_region.geojson'
    OPENSHA_ONLY = [OPENSHA_SECT_POLYS_PATH, OPENSHA_GRID_REGION_PATH]

    DATAFRAMES = InversionSolutionFile.DATAFRAMES + [
        COMPOSITE_RATES_PATH,
        AGGREGATE_RATES_PATH,
        FAST_INDICES_PATH,
    ]

    def __init__(self) -> None:
        self._rates: Optional[pd.DataFrame] = None
        super().__init__()

    def set_props(
        self, composite_rates, aggregate_rates, ruptures, indices, fault_sections, fault_regime, average_slips
    ):
        self._composite_rates = composite_rates
        self._aggregate_rates = aggregate_rates

        # Now we need a rates table, structured correctly, with weights from the aggregate_rates
        rates = self.aggregate_rates.drop(columns=['rate_max', 'rate_min', 'rate_count', 'fault_system']).rename(
            columns={"rate_weighted_mean": "Annual Rate"}
        )
        # print(self.aggregate_rates.info())
        # assert 0
        super().set_props(rates, ruptures, indices, fault_sections, average_slips)

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        data_to_zip_direct(zip_archive, self.composite_rates.to_csv(index=reindex), self.COMPOSITE_RATES_PATH)
        data_to_zip_direct(zip_archive, self.aggregate_rates.to_csv(index=reindex), self.AGGREGATE_RATES_PATH)
        if self._fast_indices is not None:
            data_to_zip_direct(zip_archive, self._fast_indices.to_csv(index=reindex), self.FAST_INDICES_PATH)

        super()._write_dataframes(zip_archive, reindex)

    def to_archive(self, archive_path, base_archive_path, compat=False):
        """
        Writes the current solution to a new zip archive, cloning data from a base archive
        """
        log.debug("%s to_archive %s" % (type(self), archive_path))
        super().to_archive(archive_path, base_archive_path, compat=False)

    @property
    def composite_rates(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(pd.Float32Dtype)
        dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
        dtypes["fault_system"] = 'category'  # pd.CategoricalDtype()
        df = self._dataframe_from_csv(self._composite_rates, self.COMPOSITE_RATES_PATH, dtypes)
        return df.set_index(["solution_id", "Rupture Index"], drop=False)

    @property
    def aggregate_rates(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(np.float32)
        dtypes = {}
        dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
        dtypes["fault_system"] = 'category'  # pd.CategoricalDtype()
        dtypes["Annual Rate"] = 'Float32'  # pd.Float32Dtype()
        df = self._dataframe_from_csv(self._aggregate_rates, self.AGGREGATE_RATES_PATH, dtypes)
        return df.set_index(["fault_system", "Rupture Index"], drop=False)

    @property
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        return self.aggregate_rates

    @property
    def fast_indices(self) -> gpd.GeoDataFrame:
        # dtypes: defaultdict = defaultdict(pd.UInt32Dtype)
        dtypes = {}
        dtypes["ruptures"] = 'UInt32'  # pd.UInt32Dtype()
        dtypes["sections"] = 'UInt32'  # pd.UInt32Dtype()
        return self._dataframe_from_csv(self._fast_indices, self.FAST_INDICES_PATH, dtypes)
