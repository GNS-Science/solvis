import zipfile
from pathlib import Path
from typing import Iterable, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import BranchSolutionProtocol, InversionSolutionProtocol


class CompositeSolution(InversionSolutionFile, InversionSolutionOperations):
    def set_props(self, rates, ruptures, indices, fault_sections, fault_regime):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._fault_regime = fault_regime

    @staticmethod
    def from_archive(archive_path: Union[Path, str]) -> 'CompositeSolution':
        new_solution = CompositeSolution()
        assert zipfile.Path(archive_path, at='ruptures/indices.csv').exists()
        new_solution._archive_path = Path(archive_path)
        return new_solution

    @staticmethod
    def filter_solution(solution: InversionSolutionProtocol, rupture_ids: npt.ArrayLike) -> 'CompositeSolution':
        rr = solution.ruptures
        ra = solution.rates
        ri = solution.indices
        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        rates = ra[ra["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()

        ns = CompositeSolution()
        ns.set_props(
            rates,
            ruptures,
            indices,
            solution.fault_sections.copy(),
            solution.fault_regime,
        )
        return ns

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates: pd.DataFrame) -> 'CompositeSolution':
        # build a new composite solution, taking solution template properties, and composite_rates
        ns = CompositeSolution()

        aggregate_rates_df = composite_rates.pivot_table(
            values='Annual Rate',
            index=['Rupture Index'],
            # columns='Rupture Index',
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
            aggregate_rates_df,
            solution.ruptures.copy(),
            solution.indices.copy(),
            solution.fault_sections.copy(),
            solution.fault_regime,
        )

        return ns

    @staticmethod
    def from_branch_solutions(solutions: Iterable[BranchSolutionProtocol]) -> 'CompositeSolution':

        # combine the rupture rates from all solutions
        all_rates_df = pd.DataFrame(columns=['Rupture Index', 'Magnitude'])
        for sb in solutions:
            # print(sb, sb.branch.inversion_solution_id)
            # print('source info', sb.rates.info())
            more_df = sb.rates.copy()  # [sb.rates['Annual Rate'] > 1e-20]
            # print('more_df info', more_df.info())
            more_df.insert(0, 'solution_id', sb.branch.inversion_solution_id)

            all_rates_df = pd.concat([all_rates_df, more_df], ignore_index=True)
        all_rates_df.solution_id = all_rates_df.solution_id.astype('category')

        return CompositeSolution.new_solution(solution=sb, composite_rates=all_rates_df)
