import logging
import zipfile
from pathlib import Path
from typing import Iterable, Union

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import pandas as pd

from .fault_system_solution_file import FaultSystemSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import BranchSolutionProtocol

log = logging.getLogger(__name__)


class FaultSystemSolution(FaultSystemSolutionFile, InversionSolutionOperations):

    _composite_rates: pd.DataFrame = ...

    # def __init__(self, source_logic_tree):
    #     self._source_logic_tree = source_logic_tree
    #     self._solutions = {}

    def set_props(self, composite_rates, aggregate_rates, ruptures, indices, fault_sections, fault_regime):
        # self._init_props()
        self._composite_rates = composite_rates
        self._aggregate_rates = aggregate_rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._fault_regime = fault_regime

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, zipfile.ZipFile]) -> 'FaultSystemSolution':
        new_solution = FaultSystemSolution()

        # TODO: sort out this weirdness
        if isinstance(instance_or_path, zipfile.ZipFile):
            assert 'ruptures/fast_indices.csv' in instance_or_path.namelist()
            assert 'composite_rates.csv' in instance_or_path.namelist()
            assert 'aggregate_rates.csv' in instance_or_path.namelist()
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
        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        composite_rates = cr[cr["Rupture Index"].isin(rupture_ids)].copy()
        aggregate_rates = ar[ar["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

        # all other solution properties are derived from those above
        ns = FaultSystemSolution()
        ns.set_props(
            composite_rates, aggregate_rates, ruptures, indices, solution.fault_sections.copy(), solution.fault_regime
        )
        ns._archive_path = solution._archive_path
        return ns

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates_df: pd.DataFrame) -> 'FaultSystemSolution':
        # build a new composite solution, taking solution template properties, and composite_rates_df
        ns = FaultSystemSolution()

        # # Remove all ruptures with no rates
        # print('COMP 0', composite_rates_df.shape)
        # print(composite_rates_df)
        # print(composite_rates_df.info())
        # composite_rates_df.to_json('diag_composite_rates_df_0.json')

        composite_rates_df = composite_rates_df[composite_rates_df["Annual Rate"] > 0]

        # TODO CBC/CDC -use the weight column on composite_rates_df to do weighted mean etc
        weighted_rate = pd.Series(composite_rates_df['Annual Rate'] * composite_rates_df['weight'], dtype="float32")
        composite_rates_df.insert(0, 'weighted_rate', weighted_rate)

        # print('COMP 1', composite_rates_df.shape)
        # print(composite_rates_df)
        # print(composite_rates_df.info())
        # composite_rates_df.to_json('diag_composite_rates_df_1.json')

        aggregate_rates_df = composite_rates_df.pivot_table(
            # values=['weighted_rate', "Annual Rate"],
            index=[
                'fault_system',
                'Rupture Index',
            ],
            aggfunc={"Annual Rate": [np.min, np.max, 'count'], "weighted_rate": np.sum},
        )

        # #aggregate_rates_df.to_json('diag_aggregate_rates.json')
        # print('AGG 0', aggregate_rates_df.shape)
        # print(aggregate_rates_df)
        # print(aggregate_rates_df.info())

        # drop the top index level
        aggregate_rates_df.columns = aggregate_rates_df.columns.get_level_values(1)

        # print('AGG', aggregate_rates_df.shape)
        # print(aggregate_rates_df)
        # print(aggregate_rates_df.info())

        # rename the aggregate columns
        aggregate_rates_df = aggregate_rates_df.reset_index().rename(
            columns={
                "amax": "rate_max",
                "amin": "rate_min",
                "count": "rate_count",
                "sum": "rate_weighted_mean",
            }
        )

        # print()
        # print('AGG 1', aggregate_rates_df.shape)
        # print(aggregate_rates_df)
        # print(aggregate_rates_df.info())

        composite_rates_df = composite_rates_df.drop(columns="weighted_rate")
        # # debugggg
        # composite_rates_df.to_json('diag_composite_rates_df.json')
        # aggregate_rates_df.to_json('diag_aggregate_rates.json')

        ns.set_props(
            composite_rates_df,
            aggregate_rates_df,
            solution.ruptures.copy(),
            solution.indices.copy(),
            solution.fault_sections.copy(),
            solution.fault_regime,
        )

        return ns

    @staticmethod
    def from_branch_solutions(solutions: Iterable[BranchSolutionProtocol]) -> 'FaultSystemSolution':

        # combine the rupture rates from all solutions
        composite_rates_df = pd.DataFrame(columns=['Rupture Index'])  # , 'Magnitude'])
        for branch_solution in solutions:
            solution_df = branch_solution.rates.copy()
            solution_df.insert(
                0, 'solution_id', branch_solution.branch.inversion_solution_id
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

        # composite_rates_df.solution_id = composite_rates_df.solution_id.astype('category')
        # composite_rates_df.fault_system = composite_rates_df.fault_system.astype('category')
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
