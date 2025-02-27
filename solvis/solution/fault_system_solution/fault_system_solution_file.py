"""
An FaultSystemSolution archive file helper.

See notes about FaultSystemSolution and OpenSHA InversionSolution archive formats.
"""

import logging
import zipfile
from functools import cache
from typing import TYPE_CHECKING, Optional, cast

import geopandas as gpd
import pandas as pd

from solvis.dochelper import inherit_docstrings

from ..inversion_solution import InversionSolutionFile, data_to_zip_direct

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from ..dataframe_models import RuptureRateSchema

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


@inherit_docstrings
class FaultSystemSolutionFile(InversionSolutionFile):
    """Class to handle the solution modular archive file form."""

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
        """
        Initializes a new FaultSystemSolutionFile instance.

        Args:
            self (FaultSystemSolutionFile): The instance to initialize.
        """
        self._rates: Optional[pd.DataFrame] = None
        super().__init__()

    def set_props(
        self, composite_rates, aggregate_rates, ruptures, indices, fault_sections, fault_regime, average_slips
    ):
        """
        Sets the properties of the FaultSystemSolutionFile instance.

        Args:
            self (FaultSystemSolutionFile): The instance to set properties for.
            composite_rates (pd.DataFrame): The composite rates dataframe.
            aggregate_rates (pd.DataFrame): The aggregate rates dataframe.
            ruptures (pd.DataFrame): The ruptures dataframe.
            indices (pd.DataFrame): The indices dataframe.
            fault_sections (pd.DataFrame): The fault sections dataframe.
            fault_regime (pd.DataFrame): The fault regime dataframe.
            average_slips (pd.DataFrame): The average slips dataframe.

        Returns:
            None
        """
        self._composite_rates = composite_rates
        self._aggregate_rates = aggregate_rates

        # Now we need a rates table, structured correctly, with weights from the aggregate_rates
        rates = aggregate_rates.drop(columns=['rate_max', 'rate_min', 'rate_count', 'fault_system']).rename(
            columns={"rate_weighted_mean": "Annual Rate"}
        )
        super().set_props(rates, ruptures, indices, fault_sections, average_slips)

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        """
        Writes the dataframes to a zip archive.

        Args:
            self (FaultSystemSolutionFile): The instance to write dataframes for.
            zip_archive (zipfile.ZipFile): The zip archive to write to.
            reindex (bool): Whether to reindex the dataframes before writing. Defaults to False.

        Returns:
            None
        """
        data_to_zip_direct(zip_archive, self.composite_rates.to_csv(index=reindex), self.COMPOSITE_RATES_PATH)
        data_to_zip_direct(zip_archive, self.aggregate_rates.to_csv(index=reindex), self.AGGREGATE_RATES_PATH)
        if self._fast_indices is not None:
            data_to_zip_direct(zip_archive, self._fast_indices.to_csv(index=reindex), self.FAST_INDICES_PATH)

        super()._write_dataframes(zip_archive, reindex)

    def to_archive(self, archive_path, base_archive_path, compat=False):
        """Writes the current solution to a new zip archive, cloning data from a base archive."""
        log.debug("%s to_archive %s" % (type(self), archive_path))
        super().to_archive(archive_path, base_archive_path, compat=False)

    @property
    def composite_rates(self) -> pd.DataFrame:
        """
        Returns the composite rates dataframe.

        Returns:
            pd.DataFrame: The composite rates dataframe.
        """
        if self._composite_rates is None:
            dtypes = {}
            dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
            dtypes["fault_system"] = 'category'  # pd.CategoricalDtype()
            self._composite_rates = self._dataframe_from_csv(self.COMPOSITE_RATES_PATH, dtypes)
        df0 = self._composite_rates.set_index(["solution_id", "Rupture Index"], drop=False)
        return df0

    @property
    def aggregate_rates(self) -> gpd.GeoDataFrame:
        """
        Returns the aggregate rates GeoDataFrame.

        Returns:
            gpd.GeoDataFrame: The aggregate rates GeoDataFrame.
        """
        if self._aggregate_rates is None:
            dtypes = {}
            dtypes["Rupture Index"] = 'UInt32'  # pd.UInt32Dtype()
            dtypes["fault_system"] = 'category'  # pd.CategoricalDtype()
            dtypes["Annual Rate"] = 'Float32'  # pd.Float32Dtype()
            self._aggregate_rates = self._dataframe_from_csv(self.AGGREGATE_RATES_PATH, dtypes)
        df0 = self._aggregate_rates.set_index(["fault_system", "Rupture Index"], drop=False)
        return df0

    @property
    def rupture_rates(self) -> 'DataFrame[RuptureRateSchema]':
        """
        Returns a GeoDataFrame containing the rupture rates.

        This property returns a pandas DataFrame with a schema of `RuptureRateSchema`, representing the
        rupture rates. The data is loaded from the `aggregate_rates` GeoDataFrame, ensuring that
        it adheres to the specified schema.

        Returns:
            DataFrame[RuptureRateSchema]: A GeoDataFrame containing the rupture rates.
        """
        return cast('DataFrame[RuptureRateSchema]', self.aggregate_rates)

    @property
    @cache
    def fast_indices(self) -> gpd.GeoDataFrame:
        """
        Retrieves the fast indices as a GeoDataFrame.

        The `fast_indices` property returns a pandas DataFrame containing
        index data for ruptures, indexed by 'sections'. This data is read from the CSV file specified by
        `FAST_INDICES_PATH`, applying specific data types to columns.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the fast indices.
        """
        dtypes = {}
        dtypes["sections"] = 'UInt32'  # pd.UInt32Dtype()
        return self._dataframe_from_csv(self.FAST_INDICES_PATH, dtypes)
