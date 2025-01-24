"""
This module handles the aggregation of InversionSolution instances which must share a common OpenSHA RuptureSet.

Classes:
    FaultSystemSolution: a class aggregating InversionSolution instances.
"""
import io
import logging
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Union, cast

import geopandas as gpd
import nzshm_model as nm
import pandas as pd

from solvis.dochelper import inherit_docstrings

from ..solution_surfaces_builder import SolutionSurfacesBuilder
from ..typing import BranchSolutionProtocol, InversionSolutionProtocol, ModelLogicTreeBranch
from .fault_system_solution_file import FaultSystemSolutionFile
from .fault_system_solution_model import FaultSystemSolutionModel

log = logging.getLogger(__name__)


@inherit_docstrings
class FaultSystemSolution(InversionSolutionProtocol):
    """A class that aggregates InversionSolution instances sharing a common OpenSHA RuptureSet.

    The class is largely interchangeable with InversionSolution, as only rupture rates
    are  affected by the aggregation.
    """

    def __init__(self, solution_file: Optional[FaultSystemSolutionFile] = None):
        self._solution_file: FaultSystemSolutionFile = solution_file or FaultSystemSolutionFile()
        self._model: FaultSystemSolutionModel = FaultSystemSolutionModel(self._solution_file)

    def to_archive(self, archive_path, base_archive_path=None, compat=False):
        self.model.enable_fast_indices()
        return self._solution_file.to_archive(archive_path, base_archive_path, compat)

    @property
    def solution_file(self) -> FaultSystemSolutionFile:
        return self._solution_file

    @property
    def model(self) -> FaultSystemSolutionModel:
        return self._model

    @property
    def fault_regime(self):
        return self._solution_file.fault_regime

    def fault_surfaces(self) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).fault_surfaces()

    def rupture_surface(self, rupture_id: int) -> gpd.GeoDataFrame:
        return SolutionSurfacesBuilder(self).rupture_surface(rupture_id)

    @staticmethod
    def from_archive(instance_or_path: Union[Path, str, io.BytesIO]) -> 'FaultSystemSolution':
        new_solution_file = FaultSystemSolutionFile()

        # TODO: sort out this weirdness
        if isinstance(instance_or_path, io.BytesIO):
            with zipfile.ZipFile(instance_or_path, 'r') as zf:
                assert 'composite_rates.csv' in zf.namelist()
                assert 'aggregate_rates.csv' in zf.namelist()
                assert 'ruptures/fast_indices.csv' in zf.namelist()
            new_solution_file._archive = instance_or_path
        else:
            assert zipfile.Path(instance_or_path, at='ruptures/fast_indices.csv').exists()
            assert zipfile.Path(instance_or_path, at='composite_rates.csv').exists()
            assert zipfile.Path(instance_or_path, at='aggregate_rates.csv').exists()
            new_solution_file._archive_path = Path(instance_or_path)
            log.debug("from_archive %s " % instance_or_path)
        return FaultSystemSolution(new_solution_file)

    @staticmethod
    def filter_solution(solution: 'InversionSolutionProtocol', rupture_ids: Iterable) -> 'FaultSystemSolution':
        # this method  is not actually used, and maybe deprecated in a future release

        solution = cast(FaultSystemSolution, solution)
        # model = solution.model
        rr = solution.solution_file.ruptures
        cr = solution.model.composite_rates
        ar = solution.model.aggregate_rates
        ri = solution.solution_file.indices.copy()
        avs = solution.solution_file.average_slips.copy()

        ruptures = rr[rr["Rupture Index"].isin(rupture_ids)].copy()
        composite_rates = cr[cr["Rupture Index"].isin(rupture_ids)].copy()
        aggregate_rates = ar[ar["Rupture Index"].isin(rupture_ids)].copy()
        indices = ri[ri["Rupture Index"].isin(rupture_ids)].copy()
        average_slips = avs[avs["Rupture Index"].isin(rupture_ids)].copy()

        # all other solution properties are derived from those above
        new_solution_file = FaultSystemSolutionFile()
        new_solution_file.set_props(
            composite_rates,
            aggregate_rates,
            ruptures,
            indices,
            solution.solution_file.fault_sections.copy(),
            solution.solution_file.fault_regime,
            average_slips,
        )

        # now copy data from the original archive
        assert solution.solution_file._archive, "Assumed _archive is not available"

        new_archive = io.BytesIO()
        with zipfile.ZipFile(new_archive, 'w') as new_zip:
            # write the core files
            with zipfile.ZipFile(solution.solution_file._archive, 'r') as zf:
                for item in zf.filelist:
                    if item.filename in solution.solution_file.DATAFRAMES:
                        log.debug(f'filter_solution() skipping copy of dataframe file: {item.filename}')
                        continue
                    if item.filename in solution.solution_file.OPENSHA_ONLY:  # drop bulky, opensha-only artefacts
                        log.debug(f'filter_solution() skipping copy of opensha only file: {item.filename}')
                        continue
                    log.debug(f'filter_solution() copying {item.filename}')
                    new_zip.writestr(item, zf.read(item.filename))

            # write the modifies tables
            new_solution_file._write_dataframes(new_zip, reindex=False)  # retain original rupture ids and structure
        new_solution_file._archive = new_archive
        new_solution_file._archive.seek(0)
        return FaultSystemSolution(new_solution_file)

    @staticmethod
    def new_solution(solution: BranchSolutionProtocol, composite_rates_df: pd.DataFrame) -> 'FaultSystemSolution':
        # build a new fault system solution, taking solution template properties, and composite_rates_df
        composite_rates_df = composite_rates_df[composite_rates_df["Annual Rate"] > 0]
        composite_rates_df.insert(
            0,
            'weighted_rate',
            pd.Series(composite_rates_df['Annual Rate'] * composite_rates_df['weight'], dtype="float32"),
        )

        aggregate_rates_df = composite_rates_df.pivot_table(
            index=['fault_system', 'Rupture Index'],
            aggfunc={"Annual Rate": ['min', 'max', 'count'], "weighted_rate": 'sum'},
        )

        # print(aggregate_rates_df.columns)
        # assert 0
        # drop the top index level
        aggregate_rates_df.columns = aggregate_rates_df.columns.get_level_values(1)
        aggregate_rates_df = aggregate_rates_df.reset_index().rename(
            columns={
                "max": "rate_max",
                "min": "rate_min",
                "count": "rate_count",
                "sum": "rate_weighted_mean",
            }
        )
        composite_rates_df = composite_rates_df.drop(columns="weighted_rate")

        fss_file = FaultSystemSolutionFile()

        fss_file.set_props(
            composite_rates_df,
            aggregate_rates_df,
            solution.solution_file.ruptures.copy(),
            solution.solution_file.indices.copy(),
            solution.solution_file.fault_sections.copy(),
            solution.solution_file.fault_regime,
            solution.solution_file.average_slips.copy(),
        )
        fss_file._archive_path = solution.solution_file.archive_path

        new_fss = FaultSystemSolution(fss_file)
        new_fss.to_archive(io.BytesIO(), solution.solution_file.archive_path)  # initialise the _archive
        return new_fss

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
                else:  # pragma: no cover
                    continue
            else:
                raise Exception("Could not find inversion solution ID for branch solution")  # pragma: no cover
        else:  # pragma: no cover
            # Fall back to v1 behaviour
            inversion_solution_id = branch.inversion_solution_id

        return inversion_solution_id

    @staticmethod
    def from_branch_solutions(solutions: Iterable[BranchSolutionProtocol]) -> 'FaultSystemSolution':

        # combine the rupture rates from all solutions
        composite_rates_df = pd.DataFrame(columns=['Rupture Index'])  # , 'Magnitude'])
        for branch_solution in solutions:
            inversion_solution_id = FaultSystemSolution.get_branch_inversion_solution_id(branch_solution.branch)

            solution_df = branch_solution.solution_file.rupture_rates.copy()
            solution_df.insert(
                0, 'solution_id', inversion_solution_id
            )  # CategoricalDtype(categories=['PUY'], ordered=False)
            solution_df.insert(0, 'rupture_set_id', branch_solution.rupture_set_id)
            solution_df.insert(0, 'weight', branch_solution.branch.weight)
            solution_df.insert(0, 'fault_system', branch_solution.fault_system)
            composite_rates_df = pd.concat([composite_rates_df, solution_df], ignore_index=True)

        return FaultSystemSolution.new_solution(solution=branch_solution, composite_rates_df=composite_rates_df)


"""
TODO: notes for fault_system_solution participation

>>> csol.rs_with_rupture_rates.head()
                            key_0 fault_system  Rupture Index  rate_max      rate_min  rate_count  rate_weighted_mean  Magnitude  Average Rake (degrees)    Area (m^2)  Length (m)  section
fault_system Rupture Index
CRU          3                  3          CRU              3  0.000047  6.097353e-06          12            0.000010   7.237556              110.000000  1.090333e+09    34817.69      0.0
             3                  3          CRU              3  0.000047  6.097353e-06          12            0.000010   7.237556              110.000000  1.090333e+09    34817.69      1.0
             3                  3          CRU              3  0.000047  6.097353e-06          12            0.000010   7.237556              110.000000  1.090333e+09    34817.69      2.0
             9                  9          CRU              9  0.000110  7.749647e-07          24            0.000032   7.285888              -95.056915  1.218684e+09    60601.45      3.0
             9                  9          CRU              9  0.000110  7.749647e-07          24            0.000032   7.285888              -95.056915  1.218684e+09    60601.45      4.0
>>> csol.composite_rates.head()
                                                        Rupture Index fault_system    weight    rupture_set_id                               solution_id  Annual Rate
solution_id                              Rupture Index
U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy 9                          9          CRU  0.016834  RmlsZToxMDAwODc=  U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy     0.000020
                                         142                      142          CRU  0.016834  RmlsZToxMDAwODc=  U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy     0.000022
                                         399                      399          CRU  0.016834  RmlsZToxMDAwODc=  U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy     0.000008
                                         607                      607          CRU  0.016834  RmlsZToxMDAwODc=  U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy     0.000010
                                         613                      613          CRU  0.016834  RmlsZToxMDAwODc=  U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy     0.000020
>>> csol.composite_rates.index
MultiIndex([('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',      9),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    142),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    399),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    607),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    613),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    626),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    628),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    634),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    721),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzIy',    722),
            ...
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 405506),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 407596),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 407597),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 408843),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 408852),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 408858),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 409076),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 409087),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 409919),
            ('U2NhbGVkSW52ZXJzaW9uU29sdXRpb246MTIwNzc4', 409995)],
           names=['solution_id', 'Rupture Index'], length=37389)
>>> csol.ruptures_with_rupture_rates.shape
(3884, 10)
>>> csol.ruptures_with_rupture_rates.head()
                           fault_system  Rupture Index  rate_max      rate_min  rate_count  rate_weighted_mean  Magnitude  Average Rake (degrees)    Area (m^2)  Length (m)
fault_system Rupture Index
CRU          3                      CRU              3  0.000047  6.097353e-06          12        1.012588e-05   7.237556              110.000000  1.090333e+09    34817.69
             9                      CRU              9  0.000110  7.749647e-07          24        3.237533e-05   7.285888              -95.056915  1.218684e+09    60601.45
             55                     CRU             55  0.000067  5.627826e-06          12        1.531652e-05   8.092601              169.242100  7.809173e+09   340323.75
             140                    CRU            140  0.000001  5.418595e-07           6        1.826545e-08   8.197684             -177.146090  9.946928e+09   455076.94
             142                    CRU            142  0.000051  2.222447e-05           6        5.750140e-06   8.225152             -172.993900  1.059636e+10   483159.47
>>> help(csol.ruptures_with_rupture_rates)

>>>
"""  # noqa
