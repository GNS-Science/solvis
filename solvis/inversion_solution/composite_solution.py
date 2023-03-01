from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd

from .inversion_solution_file import InversionSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .solution_surfaces_builder import SolutionSurfacesBuilder
from .typing import BranchSolutionProtocol, InversionSolutionProtocol


class CompositeSolution(InversionSolutionFile, InversionSolutionOperations, InversionSolutionProtocol):
    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    def set_props(self, rates, ruptures, indices, fault_sections, fault_regime):
        # self._init_props()
        self._rates = rates
        self._ruptures = ruptures
        self._fault_sections = fault_sections
        self._indices = indices
        self._fault_regime = fault_regime

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates: pd.DataFrame) -> 'CompositeSolution':
        # build a new composite solution, taking solution template properties, and composite_rates
        ns = CompositeSolution()

        aggregate_rates_df = composite_rates.pivot_table(
            values='Annual Rate', index=['Rupture Index'], aggfunc={"Annual Rate": [np.min, np.mean, np.max, 'count']}
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

        # combine the rupture rates from all solutinos
        all_rates_df = pd.DataFrame(columns=['Rupture Index', 'Magnitude'])
        for sb in solutions:
            # print(sb, sb.branch.inversion_solution_id)
            more_df = sb.rates[sb.rates['Annual Rate'] > 0]
            more_df.insert(0, 'solution_id', sb.branch.inversion_solution_id)
            # if not isinstance(all_rates_df, pd.DataFrame):
            #     all_rates_df = pd.concat([more_df], ignore_index=True)
            # else:
            all_rates_df = pd.concat([all_rates_df, more_df], ignore_index=True)
        all_rates_df.solution_id = all_rates_df.solution_id.astype('category')

        return CompositeSolution.new_solution(solution=sb, composite_rates=all_rates_df)
