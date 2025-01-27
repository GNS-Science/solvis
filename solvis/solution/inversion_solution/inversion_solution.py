"""
This module handles the standard output of an OpenSHA grand inversion.

Classes:
    InversionSolution: A python interface for an OpenSHA Inversion Solution archive.
    BranchInversionSolution: A subclass of InversionSolution with some logic tree branch attributes.

Examples:
    ```py
    >>> solution = solvis.InversionSolution.from_archive(filename)
    >>> rupture_ids = solvis.filter.FilterRuptureIds(solution)\\
            .for_magnitude(min_mag=5.75, max_mag=6.25)
    >>>
    >>> rates = solution.section_participation_rates(rupture_ids)
    ```
"""
import io
import logging
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional, Union, cast

import geopandas as gpd
import pandas as pd

from solvis.dochelper import inherit_docstrings
from solvis.filter import FilterSubsectionIds

from ..solution_surfaces_builder import SolutionSurfacesBuilder
from ..typing import InversionSolutionProtocol, ModelLogicTreeBranch
from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_model import InversionSolutionModel

if TYPE_CHECKING:
    from pandera.typing import DataFrame

    from .dataframe_models import ParentFaultParticipationSchema, SectionParticipationSchema

log = logging.getLogger(__name__)


@inherit_docstrings
class InversionSolution(InversionSolutionProtocol):
    """A python interface for an OpenSHA Inversion Solution archive.

    Attributes:
     model: the dataframes model of the solution.
     solution_file: the archive file instance.
     fault_regime: the type of fault system.

    Methods:
     from_archive: deserialise an instance from zip archive.
     to_archive: serialise an instance to a zip archive.
     filter_solution: get a new InversionSolution instance, filtered by rupture ids.
     rupture_surface: get a geopandas dataframe representing a rutpure surface.
     fault_surfaces: get a geopandas dataframe representing teh fault surfaces.
     section_participation_rates: calculate the 'participation rate' for fault subsections.
     fault_participation_rates: calculate the 'participation rate' for parent faults.
    """

    # Docstrings for most methods are found in the `InversionSolutionProtocol` class.

    def __init__(self, solution_file: Optional[InversionSolutionFile] = None):
        self._solution_file = solution_file or InversionSolutionFile()
        self._model = InversionSolutionModel(self._solution_file)

    @property
    def model(self) -> InversionSolutionModel:
        return self._model

    @property
    def solution_file(self) -> InversionSolutionFile:
        return self._solution_file

    @property
    def fault_regime(self) -> str:
        return self._solution_file.fault_regime

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'InversionSolution':
        new_solution_file = InversionSolutionFile()

        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/indices.csv' in zf.namelist()
            new_solution_file._archive = instance_or_path
        else:
            assert Path(instance_or_path).exists()
            assert zipfile.Path(instance_or_path, at='ruptures/indices.csv').exists()
            new_solution_file._archive_path = Path(instance_or_path)
        return InversionSolution(new_solution_file)

    @staticmethod
    def filter_solution(solution: 'InversionSolutionProtocol', rupture_ids: Iterable[int]) -> 'InversionSolution':
        # model = solution.model
        rr = solution.solution_file.ruptures
        ra = solution.solution_file.rupture_rates
        ri = solution.solution_file.indices
        avs = solution.solution_file.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        ns = InversionSolution()

        ns.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), average_slips
        )

        ## TODO:  there should be a new in-memory archive ??
        ns.solution_file._archive_path = solution.solution_file.archive_path

        return ns

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[SectionParticipationSchema]':
        """Calculate the 'participation rate' for fault subsections.

        Participation rate for each section is the the sum of rupture rates for the ruptures involving that section.

        Args:
            subsection_ids: the list of subsection_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka `Conditional Participation`).

        Notes:
         - Passing a non empty `subsection_ids` will not affect the rates, only the subsections for
           which rates are returned.
         - Passing a non empty `rupture_ids` will affect the rates, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in the rates of e.g. ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        rate_column = self.model.rate_column_name()
        t0 = time.perf_counter()
        df0 = cast(pd.DataFrame, self.model.rs_with_rupture_rates)

        log.info(f"df0 shape: {df0.shape}")

        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        t1 = time.perf_counter()
        log.info(f'apply section filter took : {t1-t0} seconds')

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        t2 = time.perf_counter()
        log.info(f'apply rupture_ids filter took : {t2-t1} seconds')

        # result = df0.pivot_table(values=rate_column, index=['section'], aggfunc='sum')
        result = df0[["section", "Rupture Index", rate_column]].groupby("section").agg('sum')
        result = result[[rate_column]]
        t3 = time.perf_counter()
        log.info(f'dataframe aggregation took : {t3-t2} seconds')
        result = result.rename(columns={rate_column: 'participation_rate'})
        return cast('DataFrame[SectionParticipationSchema]', result)

    def fault_participation_rates(
        self, parent_fault_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ) -> 'DataFrame[ParentFaultParticipationSchema]':
        """Calculate the 'participation rate' for parent faults.

        Participation rate for each parent fault is the the sum of rupture rates for the
        ruptures involving that parent fault.

        Args:
            parent_fault_ids: the list of parent_fault_ids to include.
            rupture_ids: calculate participation using only these ruptures (aka Conditional Participation).

        Notes:
         - Passing `parent_fault_ids` will not affect the rate calculation, only the parent faults
           for which rates are returned.
         - Passing `rupture_ids` will affect the rates, as only the specified ruptures
           will be included in the sum.
           This is referred to as the `conditional participation rate` which might be used when you are
           only interested in e.g. the rates of ruptures in a particular magnitude range.

        Returns:
            pd.DataFrame: a participation rates dataframe
        """
        subsection_ids = FilterSubsectionIds(self).for_parent_fault_ids(parent_fault_ids) if parent_fault_ids else None

        rate_column = self.model.rate_column_name()

        df0 = cast(pd.DataFrame, self.model.rs_with_rupture_rates)
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self.solution_file.fault_sections[['ParentID']], on='section')
        result = (
            df1[["ParentID", "Rupture Index", rate_column]]
            .rename(columns={rate_column: 'participation_rate'})
            .reset_index(drop=True)
            .groupby(["ParentID", "Rupture Index"])
            .agg('first')
            .groupby("ParentID")
            .agg('sum')
        )
        return cast('DataFrame[ParentFaultParticipationSchema]', result)


class BranchInversionSolution(InversionSolution):
    """Extend InversionSolution with the branch attributes:

    Attributes:
        branch: a logic tree branch instance.
        fault_system: A string representing the fault System (e.g `CRU`, 'HIK`).
        rupture_set_id: a string ID for the rupture_set_id.

    Methods:
        new_branch_solution: produce a new `BranchInversionSolution` instance.

    Todo:
        - can this functionality be done more simply and/or
        - can we make better use of latest `nzshm_model` and its' dataclasses.

    """

    branch: ModelLogicTreeBranch
    fault_system: Union[str, None] = ""
    rupture_set_id: Union[str, None] = ""

    @staticmethod
    def new_branch_solution(
        solution: InversionSolution, branch: ModelLogicTreeBranch, fault_system: str, rupture_set_id: str
    ) -> 'BranchInversionSolution':
        """Produce a new `BranchInversionSolution` instance with the given arguments.

        Args:
            solution: a solution instance.
            branch: a Logic tree branch instance (including branch metadata, weight, sources, etc).
            fault_system: a string representing the fault system (e.g `CRU`, 'HIK`).
            rupture_set_id: id for the rupture_set_id.
        """
        ruptures = solution.solution_file.ruptures.copy()
        rates = solution.solution_file.rupture_rates.copy()
        indices = solution.solution_file.indices.copy()

        # print(solution.solution_file.fault_sections)
        # assert 0

        bis = BranchInversionSolution()
        bis.branch = branch
        bis.fault_system = fault_system
        bis.rupture_set_id = rupture_set_id
        bis.solution_file.set_props(
            rates, ruptures, indices, solution.solution_file.fault_sections.copy(), solution.solution_file.average_slips
        )
        bis.solution_file._archive_path = solution.solution_file._archive_path
        return bis

    def __repr__(self):
        return f"{self.__class__}({self.fault_system})"
