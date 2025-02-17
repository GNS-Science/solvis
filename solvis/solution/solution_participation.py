"""Module providing the SolutionParticipation helper class."""

import logging
import time
from typing import TYPE_CHECKING, Iterable, Optional, cast

import pandas as pd

from solvis.filter import FilterParentFaultIds, FilterSubsectionIds
from solvis.solution import named_fault

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from solvis.solution import dataframe_models

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from solvis import InversionSolution


class SolutionParticipation:
    r"""Calculate solution participation rates.

    Calculates rupture participation rates at either section or fault levels, with the option
    to make the rates `Conditional Participation` by specifying a subset of the available ruptures.

    Examples:
        ```py
        >>> sol = solvis.InversionSolution.from_archive(filename)
        >>>
        >>> rate = SolutionParticipation(sol)\
            .fault_participation_rates(['Vernon 4', 'Alpine: Jacksons to Kaniere'])
        >>>
        ```

    Methods:
        section_participation_rates:  get rates for fault sections.
        fault_participation_rates: get rates for parent faults.
        named_fault_participation_rates: get rates for named faults
    """

    def __init__(self, solution: 'InversionSolution'):
        """Instantiate a new instance.

        Args:
            solution: the subject solution instance.
        """
        self._solution = solution

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[dataframe_models.SectionParticipationSchema]':
        """Calculate the 'participation rate' for fault subsections.

        Participation rate for each section is the the sum of rupture rates for the ruptures involving that section.

        Args:
            subsection_ids: the list of subsection_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka `Conditional Participation`).

        Notes:
         - Passing a non empty `subsection_ids` does not affect the rates, only the subsections for
           which rates are returned.
         - Passing a non empty `rupture_ids` affects the rate calculation, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in the rates of e.g. ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        rate_column = self._solution.model.rate_column_name()
        t0 = time.perf_counter()
        df0 = cast(pd.DataFrame, self._solution.model.rs_with_rupture_rates)

        log.info(f"df0 shape: {df0.shape}")

        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        t1 = time.perf_counter()
        log.info(f'apply section filter took : {t1 - t0} seconds')

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        t2 = time.perf_counter()
        log.info(f'apply rupture_ids filter took : {t2 - t1} seconds')

        # result = df0.pivot_table(values=rate_column, index=['section'], aggfunc='sum')
        result = df0[["section", "Rupture Index", rate_column]].groupby("section").agg('sum')
        result = result[[rate_column]]
        t3 = time.perf_counter()
        log.info(f'dataframe aggregation took : {t3 - t2} seconds')
        result = result.rename(columns={rate_column: 'participation_rate'})
        return cast('DataFrame[dataframe_models.SectionParticipationSchema]', result)

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[dataframe_models.ParentFaultParticipationSchema]':
        """Calculate the 'participation rate' for parent faults.

        Participation rate for each parent fault is the the sum of rupture rates for the
        ruptures involving that parent fault.

        Args:
            parent_fault_ids: the list of parent_fault_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka Conditional Participation).

        Notes:
         - Passing `parent_fault_ids` does not affect the rate calculation, only the parent faults
           for which rates are returned.
         - Passing `rupture_ids` affects the rate calculation, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in e.g. the rates of ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        subsection_ids = (
            FilterSubsectionIds(self._solution).for_parent_fault_ids(parent_fault_ids) if parent_fault_ids else None
        )

        df0 = cast(pd.DataFrame, self._solution.model.rs_with_rupture_rates)
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self._solution.solution_file.fault_sections[['ParentID']], on='section')
        rate_column = self._solution.model.rate_column_name()
        result = (
            df1[["ParentID", "Rupture Index", rate_column]]
            .rename(columns={rate_column: 'participation_rate'})
            .reset_index(drop=True)
            .groupby(["ParentID", "Rupture Index"])
            .agg('first')
            .groupby("ParentID")
            .agg('sum')
        )
        return cast('DataFrame[dataframe_models.ParentFaultParticipationSchema]', result)

    def named_fault_participation_rates(
        self, named_fault_names: Optional[Iterable[str]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[dataframe_models.NamedFaultParticipationSchema]':
        """Calculate the 'participation rate' for parent faults.

        Participation rate for each named fault is the the sum of rupture rates for the
        ruptures involving that fault.

        Args:
            named_fault_names: the list of named_fault_names to include.
            rupture_ids: calculate participation using only these ruptures (aka Conditional Participation).

        Notes:
         - Passing `named_fault_names` does not affect the rate calculation, only the faults
           for which rates are returned.
         - Passing `rupture_ids` affects the rate calculation, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in e.g. the rates of ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        parent_fault_ids = (
            FilterParentFaultIds(self._solution).for_named_fault_names(named_fault_names) if named_fault_names else None
        )

        subsection_ids = (
            FilterSubsectionIds(self._solution).for_parent_fault_ids(parent_fault_ids) if parent_fault_ids else None
        )

        df0 = cast(pd.DataFrame, self._solution.model.rs_with_rupture_rates)
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self._solution.solution_file.fault_sections[['ParentID']], on='section')
        df2 = df1.join(named_fault.named_fault_for_parent_ids_table(), 'ParentID', how='outer')
        df2 = df2.drop(columns=['ParentID'])

        rate_column = self._solution.model.rate_column_name()

        result = (
            df2[["named_fault_name", "Rupture Index", rate_column]]
            .rename(columns={rate_column: 'participation_rate'})
            .reset_index(drop=True)
            .groupby(["named_fault_name", "Rupture Index"])
            .agg('first')
            .groupby("named_fault_name")
            .agg('sum')
        )
        return cast('DataFrame[dataframe_models.NamedFaultParticipationSchema]', result)
