import io
import logging
import zipfile
from pathlib import Path
from typing import Iterable, Union

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import nzshm_model as nm
import pandas as pd

from .fault_system_solution_file import FaultSystemSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import BranchSolutionProtocol, ModelLogicTreeBranch

log = logging.getLogger(__name__)


class FaultSystemSolution(FaultSystemSolutionFile, InversionSolutionOperations):

    _composite_rates: pd.DataFrame = ...

    def set_props(
        self, composite_rates, aggregate_rates, ruptures, indices, fault_sections, fault_regime, average_slips
    ):
        # self._init_props()
        self._composite_rates = composite_rates
        self._aggregate_rates = aggregate_rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._fault_regime = fault_regime
        self._average_slips = average_slips

        # Now we need a rates table, structured correctly, with weights from the aggregate_rates
        rates = self.aggregate_rates.drop(columns=['rate_max', 'rate_min', 'rate_count', 'fault_system']).rename(
            columns={"rate_weighted_mean": "Annual Rate"}
        )
        self._rates = rates

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'FaultSystemSolution':
        new_solution = FaultSystemSolution()

        # TODO: sort out this weirdness
        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'ruptures/fast_indices.csv' in zf.namelist()
                assert 'composite_rates.csv' in zf.namelist()
                assert 'aggregate_rates.csv' in zf.namelist()
            new_solution._archive = instance_or_path
        else:
            assert zipfile.Path(instance_or_path, at='ruptures/fast_indices.csv').exists()
            assert zipfile.Path(instance_or_path, at='composite_rates.csv').exists()
            assert zipfile.Path(instance_or_path, at='aggregate_rates.csv').exists()
            new_solution._archive_path = Path(instance_or_path)
            log.debug("from_archive %s " % instance_or_path)
        return new_solution

    @staticmethod
    def filter_solution(solution: 'FaultSystemSolution', rupture_ids: npt.ArrayLike) -> 'FaultSystemSolution':
        rr = solution.ruptures
        cr = solution.composite_rates
        ar = solution.aggregate_rates
        ri = solution.indices
        avs = solution.average_slips

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        composite_rates = cr[cr["Rupture Index"].isin(rupture_ids)].copy()
        aggregate_rates = ar[ar["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        # all other solution properties are derived from those above
        ns = FaultSystemSolution()
        ns.set_props(
            composite_rates,
            aggregate_rates,
            ruptures,
            indices,
            solution.fault_sections.copy(),
            solution.fault_regime,
            average_slips,
        )
        # ns._archive_path = None
        ns.enable_fast_indices()
        # copy the original archive, if it exists
        # TODO: does the archive needs filtering applied?? see to_archive()
        if solution._archive:
            new_archive = io.BytesIO()
            with zipfile.ZipFile(new_archive, 'w') as new_zip:
                # write the core files
                with zipfile.ZipFile(solution._archive, 'r') as zf:
                    for item in zf.filelist:
                        if item.filename in solution.DATAFRAMES:
                            continue
                        if item.filename in solution.OPENSHA_ONLY:  # drop bulky, opensha-only artefacts
                            continue
                        new_zip.writestr(item, zf.read(item.filename))
                # write the modifies tables
                ns._write_dataframes(new_zip, reindex=False)  # retain original rupture ids and structure
            ns._archive = new_archive
            ns._archive.seek(0)
        return ns

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates_df: pd.DataFrame) -> 'FaultSystemSolution':
        # build a new composite solution, taking solution template properties, and composite_rates_df
        ns = FaultSystemSolution()

        composite_rates_df = composite_rates_df[composite_rates_df["Annual Rate"] > 0]
        composite_rates_df.insert(
            0,
            'weighted_rate',
            pd.Series(composite_rates_df['Annual Rate'] * composite_rates_df['weight'], dtype="float32"),
        )

        aggregate_rates_df = composite_rates_df.pivot_table(
            index=['fault_system', 'Rupture Index'],
            aggfunc={"Annual Rate": [np.min, np.max, 'count'], "weighted_rate": np.sum},
        )

        # drop the top index level
        aggregate_rates_df.columns = aggregate_rates_df.columns.get_level_values(1)
        aggregate_rates_df = aggregate_rates_df.reset_index().rename(
            columns={
                "amax": "rate_max",
                "amin": "rate_min",
                "count": "rate_count",
                "sum": "rate_weighted_mean",
            }
        )
        composite_rates_df = composite_rates_df.drop(columns="weighted_rate")

        ns.set_props(
            composite_rates_df,
            aggregate_rates_df,
            solution.ruptures.copy(),
            solution.indices.copy(),
            solution.fault_sections.copy(),
            solution.fault_regime,
            solution.average_slips.copy(),
        )
        return ns

    @staticmethod
    def get_branch_inversion_solution_id(branch: ModelLogicTreeBranch) -> str:
        """
        Return a single inversion solution ID from an NZSHM Model logic tree branch (v1 or v2).

        Note:
            This distinction may go away in future versions, simplifying this issue:
            https://github.com/GNS-Science/nzshm-model/issues/81
        """
        if isinstance(branch, nm.logic_tree.source_logic_tree.version2.logic_tree.SourceBranch):
            # NZSHM Model 0.6: v2 branches take inversion ID from first InversionSource
            for source in branch.sources:
                if source.type == "inversion":
                    inversion_solution_id = source.inversion_id
                    break
            else:
                raise Exception("Could not find inversion solution ID for branch solution")
        else:
            # Fall back to v1 behaviour
            inversion_solution_id = branch.inversion_solution_id

        return inversion_solution_id

    @staticmethod
    def from_branch_solutions(solutions: Iterable[BranchSolutionProtocol]) -> 'FaultSystemSolution':

        # combine the rupture rates from all solutions
        composite_rates_df = pd.DataFrame(columns=['Rupture Index'])  # , 'Magnitude'])
        for branch_solution in solutions:
            inversion_solution_id = FaultSystemSolution.get_branch_inversion_solution_id(branch_solution.branch)

            solution_df = branch_solution.rupture_rates.copy()
            solution_df.insert(
                0, 'solution_id', inversion_solution_id
            )  # CategoricalDtype(categories=['PUY'], ordered=False)
            solution_df.insert(
                0, 'rupture_set_id', branch_solution.rupture_set_id
            )  # , pd.Series(branch_solution.rupture_set_id, dtype='category'))
            solution_df.insert(0, 'weight', branch_solution.branch.weight)
            solution_df.insert(
                0, 'fault_system', branch_solution.fault_system
            )  # , pd.Series(branch_solution.fault_system, dtype='category'))
            composite_rates_df = pd.concat([composite_rates_df, solution_df], ignore_index=True)

            # print('dims', composite_rates_df.shape, solution_df.shape)
        return FaultSystemSolution.new_solution(solution=branch_solution, composite_rates_df=composite_rates_df)

    @property
    def rupture_sections(self) -> gpd.GeoDataFrame:
        """FSS overrides InversionSolutionOperations so we can use fast_indices"""

        if self._fast_indices is None:
            try:
                self._fast_indices = self.fast_indices
                log.debug("loaded fast indices")
            except Exception:
                log.info("rupture_sections() building fast indices")
                self._fast_indices = self.build_rupture_sections()

        if self._rupture_sections is None:
            self._rupture_sections = self._fast_indices

        return self._rupture_sections

    def enable_fast_indices(self) -> bool:
        """make sure that the fast_indices dataframe is available at serialisation time"""
        rs = self.rupture_sections  # noqa
        return self._fast_indices is not None
