"""
This module defines the class `InversionSolutionModel`.

The `InversionSolutionModel` class provides methods to build pandas dataframes
from the raw dataframes available via the `InversionSolutionFile` class.
"""

import logging
import time
from typing import TYPE_CHECKING, List, Optional, cast

import geopandas as gpd
import pandas as pd

from solvis.solution.typing import InversionSolutionModelProtocol

from .inversion_solution_file import InversionSolutionFile

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from .dataframe_models import (  # FaultSectionSchema,
        FaultSectionRuptureRateSchema,
        FaultSectionWithSolutionSlipRate,
        RuptureSectionSchema,
        RuptureSectionsWithRuptureRatesSchema,
        RupturesWithRuptureRatesSchema,
    )

log = logging.getLogger(__name__)


class InversionSolutionModel(InversionSolutionModelProtocol):
    """
    helper methods for analysis of InversionSolutionProtocol subtypes.

    Deprecated:
     the following methods are replaced by solvis.filter classes.

     - get_rupture_ids_for_fault_names
     - get_rupture_ids_for_location_radius
     - get_rupture_ids_for_parent_fault
     - get_rupture_ids_intersecting
     - get_ruptures_for_parent_fault
     - get_ruptures_intersecting
     - get_solution_slip_rates_for_parent
    """

    def __init__(self, solution_file: InversionSolutionFile) -> None:
        self._solution_file = solution_file
        self._rs_with_rupture_rates: Optional[pd.DataFrame] = None
        self._ruptures_with_rupture_rates: Optional[pd.DataFrame] = None
        self._rupture_sections: Optional[gpd.GeoDataFrame] = None
        self._fs_with_rates: Optional[pd.DataFrame] = None
        self._fs_with_soln_rates: Optional[pd.DataFrame] = None
        self._fault_sections: Optional[pd.DataFrame] = None

    @property
    def solution_file(self) -> InversionSolutionFile:
        return self._solution_file

    # ###
    # # These attributes are 'hoisted' from the _solution_file instance
    # #
    # # those that return dataframes may be migrated to the model -> InversionSolutionModel
    # ####
    # @property
    # def average_slips(self):
    #     return self._solution_file.average_slips

    # @property
    # def section_target_slip_rates(self):
    #     return self._solution_file.section_target_slip_rates

    # @property
    # def fault_sections(self):
    #     return self._solution_file.fault_sections

    # # @property
    # # def indices(self):
    # #     return self._solution_file.indices

    # @property
    # def ruptures(self):
    #     return self._solution_file.ruptures

    # @property
    # def rupture_rates(self):
    #     return self._solution_file.rupture_rates

    def rate_column_name(self) -> str:
        """Get the appropriate rate_column name.

        Returns:
            rate_column: "Annual Rate" or rate_weighted_mean"
        """
        return (
            "Annual Rate" if self._solution_file.__class__.__name__ == "InversionSolutionFile" else "rate_weighted_mean"
        )

    @property
    def rupture_sections(self) -> 'DataFrame[RuptureSectionSchema]':
        """
        Calculate and cache the permutations of rupture_id and section_id.

        Returns:
            pd.DataFrame: a pandas dataframe
        """
        if self._rupture_sections is not None:
            return cast('DataFrame[RuptureSectionSchema]', self._rupture_sections)

        self._rupture_sections = self.build_rupture_sections()
        return cast('DataFrame[RuptureSectionSchema]', self._rupture_sections)

    def build_rupture_sections(self) -> 'DataFrame[RuptureSectionSchema]':

        tic = time.perf_counter()

        rs = self.solution_file.indices  # _dataframe_from_csv(self._rupture_sections, 'ruptures/indices.csv').copy()

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
        return cast('DataFrame[RuptureSectionSchema]', df2)

    @property
    def fault_sections_with_rupture_rates(self) -> 'DataFrame[FaultSectionRuptureRateSchema]':
        """
        Calculate and cache the fault sections and their rupture rates.

        Returns:
            a gpd.GeoDataFrame
        """
        # assert 0
        if self._fs_with_rates is not None:
            print(self._fs_with_rates.columns)
            # assert 0
            return cast('DataFrame[FaultSectionRuptureRateSchema]', self._fs_with_rates)

        tic = time.perf_counter()
        print(self.rs_with_rupture_rates)
        assert self.rs_with_rupture_rates is not None
        self._fs_with_rates = self.rs_with_rupture_rates.join(self.solution_file.fault_sections, 'section', how='inner')
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
        return cast('DataFrame[FaultSectionRuptureRateSchema]', self._fs_with_rates)

    @property
    def parent_fault_names(self) -> List[str]:
        return sorted(self.solution_file.fault_sections.ParentName.unique())

    @property
    def fault_sections_with_solution_slip_rates(self) -> 'DataFrame[FaultSectionWithSolutionSlipRate]':
        """Calculate and cache fault sections and their solution slip rates.

        Solution slip rate combines the inversion inputs (avg slips), and the inversion solution (rupture rates).

        Returns:
            a gpd.GeoDataFrame
        """
        if self._fs_with_soln_rates is not None:
            return cast('DataFrame[FaultSectionWithSolutionSlipRate]', self._fs_with_soln_rates)

        tic = time.perf_counter()
        self._fs_with_soln_rates = self._get_soln_rates()
        toc = time.perf_counter()
        log.debug('fault_sections_with_soilution_rates: time to calculate solution rates: %2.3f seconds' % (toc - tic))
        return cast('DataFrame[FaultSectionWithSolutionSlipRate]', self._fs_with_soln_rates)

    def _get_soln_rates(self) -> 'DataFrame[FaultSectionWithSolutionSlipRate]':
        """Get a dataframe joining ruptures and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        average_slips = self.solution_file.average_slips
        # for every subsection, find the ruptures on it
        fault_sections_wr = self.solution_file.fault_sections.copy()
        for idx, fault_section in self.solution_file.fault_sections.iterrows():
            fault_id = fault_section['FaultID']
            fswr_gt0 = self.fault_sections_with_rupture_rates[
                (self.fault_sections_with_rupture_rates['FaultID'] == fault_id)
                & (self.fault_sections_with_rupture_rates['Annual Rate'] > 0.0)
            ]
            fault_sections_wr.loc[idx, 'Solution Slip Rate'] = sum(  # type: ignore
                fswr_gt0['Annual Rate'] * average_slips.loc[fswr_gt0['Rupture Index']]['Average Slip (m)']
            )

        return cast('DataFrame[FaultSectionWithSolutionSlipRate]', fault_sections_wr)

    @property
    def rs_with_rupture_rates(self) -> 'DataFrame[RuptureSectionsWithRuptureRatesSchema]':
        """Get a dataframe joining rupture_sections and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._rs_with_rupture_rates is not None:
            return cast('DataFrame[RuptureSectionsWithRuptureRatesSchema]', self._rs_with_rupture_rates)

        tic = time.perf_counter()
        # df_rupt_rate = self.ruptures.join(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._rs_with_rupture_rates = self.ruptures_with_rupture_rates.join(
            self.rupture_sections.set_index("rupture"),
            on=self.ruptures_with_rupture_rates["Rupture Index"],  # type: ignore
        )

        toc = time.perf_counter()
        log.info(
            (
                'rs_with_rupture_rates: time to load ruptures_with_rupture_rates '
                'and join with rupture_sections: %2.3f seconds'
            )
            % (toc - tic)
        )
        return cast('DataFrame[RuptureSectionsWithRuptureRatesSchema]', self._rs_with_rupture_rates)

    @property
    def ruptures_with_rupture_rates(self) -> 'DataFrame[RupturesWithRuptureRatesSchema]':
        """Get a dataframe joining ruptures and rupture_rates.

        Returns:
            a gpd.GeoDataFrame
        """
        if self._ruptures_with_rupture_rates is not None:
            return cast('DataFrame[RupturesWithRuptureRatesSchema]', self._ruptures_with_rupture_rates)

        tic = time.perf_counter()
        # print(self.rupture_rates.drop(self.rupture_rates.iloc[:, :1], axis=1))
        self._ruptures_with_rupture_rates = self.solution_file.rupture_rates.join(
            self.solution_file.ruptures.drop(columns="Rupture Index"),
            on=self.solution_file.rupture_rates["Rupture Index"],  # type: ignore
        )
        if 'key_0' in self._ruptures_with_rupture_rates.columns:  # pragma: no cover (can this be dropped?)
            self._ruptures_with_rupture_rates.drop(columns=['key_0'], inplace=True)
        toc = time.perf_counter()
        log.debug(
            'ruptures_with_rupture_rates(): time to load rates and join with ruptures: %2.3f seconds' % (toc - tic)
        )
        return cast('DataFrame[RupturesWithRuptureRatesSchema]', self._ruptures_with_rupture_rates)
