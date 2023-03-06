import zipfile
from pathlib import Path
from typing import Iterable, Union

import numpy as np
import pandas as pd

from .fault_system_solution_file import FaultSystemSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import BranchSolutionProtocol


class FaultSystemSolution(FaultSystemSolutionFile, InversionSolutionOperations):

    _composite_rates: pd.DataFrame = ...

    def set_props(self, composite_rates, rates, ruptures, indices, fault_sections, fault_regime):
        # self._init_props()
        self._composite_rates = composite_rates
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._fault_regime = fault_regime

    @staticmethod
    def from_archive(archive_path: Union[Path, str]) -> 'FaultSystemSolution':
        new_solution = FaultSystemSolution()
        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        new_solution._archive_path = Path(archive_path)
        return new_solution

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates: pd.DataFrame) -> 'FaultSystemSolution':
        # build a new composite solution, taking solution template properties, and composite_rates
        ns = FaultSystemSolution()

        # TODO CBC/CDC -use the weight column on composite_rates to do weighted mean etc
        aggregate_rates_df = composite_rates.pivot_table(
            values='Annual Rate',
            index=[
                'fault_system',
                'Rupture Index',
            ],
            aggfunc={"Annual Rate": [np.min, np.mean, np.max, np.median, 'count']},
        )

        aggregate_rates_df = aggregate_rates_df.reset_index().rename(
            columns={
                "amax": "rate_max",
                "amin": "rate_min",
                "count": "rate_count",
                "mean": "rate_mean",
                "median": "rate_median",
            }
        )

        ns.set_props(
            composite_rates,
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
        all_rates_df = pd.DataFrame(columns=['Rupture Index'])  # , 'Magnitude'])
        for sb in solutions:
            solution_df = sb.rates.copy()
            solution_df.insert(0, 'solution_id', sb.branch.inversion_solution_id)
            solution_df.insert(0, 'rupture_set_id', sb.rupture_set_id)
            solution_df.insert(0, 'weight', sb.branch.weight)
            solution_df.insert(0, 'fault_system', sb.fault_system)
            all_rates_df = pd.concat([all_rates_df, solution_df], ignore_index=True)

            print('dims', all_rates_df.shape, solution_df.shape)

        all_rates_df.solution_id = all_rates_df.solution_id.astype('category')

        return FaultSystemSolution.new_solution(solution=sb, composite_rates=all_rates_df)
