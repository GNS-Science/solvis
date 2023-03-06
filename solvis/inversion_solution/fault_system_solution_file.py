import zipfile

import geopandas as gpd
import pandas as pd

from .inversion_solution_file import InversionSolutionFile, data_to_zip_direct, reindex_dataframe

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

    COMPOSITE_RATES_PATH = 'composite_rates.csv'
    DATAFRAMES = [
        InversionSolutionFile.RATES_PATH,
        InversionSolutionFile.RUPTS_PATH,
        InversionSolutionFile.INDICES_PATH,
        COMPOSITE_RATES_PATH,
    ]

    def _write_dataframes(self, zip_archive: zipfile.ZipFile, reindex: bool = False):
        if reindex:
            data_to_zip_direct(
                zip_archive, reindex_dataframe(self._composite_rates).to_csv(), self.COMPOSITE_RATES_PATH
            )
            data_to_zip_direct(zip_archive, reindex_dataframe(self._rates).to_csv(), self.RATES_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._ruptures).to_csv(), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, reindex_dataframe(self._indices).to_csv(), self.INDICES_PATH)
        else:
            data_to_zip_direct(zip_archive, self._composite_rates.to_csv(), self.COMPOSITE_RATES_PATH)
            data_to_zip_direct(zip_archive, self._rates.to_csv(index=False), self.RATES_PATH)
            data_to_zip_direct(zip_archive, self._ruptures.to_csv(), self.RUPTS_PATH)
            data_to_zip_direct(zip_archive, self._indices.to_csv(), self.INDICES_PATH)

    @property
    def composite_rates(self) -> gpd.GeoDataFrame:
        return self._dataframe_from_csv(self._composite_rates, self.COMPOSITE_RATES_PATH)
