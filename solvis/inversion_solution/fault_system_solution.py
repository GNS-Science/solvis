"""
This module handles the aggregation of InversionSolution instances which must share a common OpenSHA RuptureSet.

Classes:
    FaultSystemSolution: a class aggregating InversionSolution instances.
"""
import io
import logging
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Union

import geopandas as gpd
import nzshm_model as nm
import pandas as pd

from .fault_system_solution_file import FaultSystemSolutionFile
from .inversion_solution_operations import InversionSolutionOperations
from .typing import BranchSolutionProtocol, ModelLogicTreeBranch

log = logging.getLogger(__name__)


class FaultSystemSolution(FaultSystemSolutionFile, InversionSolutionOperations):
    """A class that aggregates InversionSolution instances sharing a common OpenSHA RuptureSet.

    The class is largely interchangeable with InversionSolution, as only rupture rates
    are  affected by the aggregation.
    """

    _composite_rates: Optional[pd.DataFrame] = None
    _rs_with_composite_rupture_rates: Optional[pd.DataFrame] = None
    _fast_indices: Optional[pd.DataFrame] = None

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
    def filter_solution(solution: 'FaultSystemSolution', rupture_ids: Iterable) -> 'FaultSystemSolution':
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
        """Get a geodataframe of the rupture sections shared by all solution instances:

        FSS overrides InversionSolutionOperations so we can use fast_indices.
        """

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

    '''
    @property
    def rs_with_composite_rupture_rates(self):
        if self._rs_with_composite_rupture_rates is not None:
            return self._rs_with_composite_rupture_rates  # pragma: no cover

        tic = time.perf_counter()

        df0 = self.composite_rates.drop(columns=["Rupture Index", 'solution_id']).reset_index()
        df0['weighted_rate'] = df0['Annual Rate'] * df0['weight']
        df1 = df0.join(self.rupture_sections.set_index("rupture"), on=df0["Rupture Index"])

        toc = time.perf_counter()
        log.info('time to build Dataframe: rs_with_composite_rupture_rates: %2.3f seconds' % (toc - tic))

        self._rs_with_composite_rupture_rates = df1
        return self._rs_with_composite_rupture_rates

    def section_participation_rates(
        self, subsection_ids: Optional[Iterable[int]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        """
        get the 'participation rate' for fault subsections.

        That is, the sum of rupture rates on the requested fault sections.
        """
        # ALERT: does this actually work if we have FSS. what is the sum of rate_weighted_mean ??
        # rate_column = "weighted_rate"  # if isinstance(self.solution, InversionSolution) else "rate_weighted_mean"

        df0 = self.rs_with_composite_rupture_rates
        # print(df0)
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]
        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        # print('section_participation_rates')
        # print(df0.columns)
        # print(df0[["Rupture Index", 'Annual Rate', 'weight', 'weighted_rate', 'section']][df0['section']==0])
        # print()

        # return df0.pivot_table(values=rate_column, index=['section'], aggfunc='sum')
        return df0.groupby("section").agg('sum')

    def fault_participation_rates(
        self, fault_names: Optional[Iterable[str]] = None, rupture_ids: Optional[Iterable[int]] = None
    ):
        """
        get the 'participation rate' for parent faults.

        That is, the sum of rupture rates on the requested parent faults.
        """
        subsection_ids = FilterSubsectionIds(self).for_parent_fault_names(fault_names) if fault_names else None

        # print(f'subsection_ids: {subsection_ids}')

        df0 = self.rs_with_composite_rupture_rates
        if subsection_ids:
            df0 = df0[df0["section"].isin(subsection_ids)]

        # print(df0)
        if rupture_ids:
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

        df1 = df0.join(self.fault_sections[['ParentID']], on='section')

        # print('df1')
        # print(df1.columns)
        # print(df1[["ParentID", "Rupture Index", 'weighted_rate', 'section']])
        # print()
        # df = (
        #     df1[["ParentID", "Rupture Index", 'weighted_rate']]
        #         .groupby(["ParentID", "Rupture Index"])
        #         .agg('first')
        # )
        # print(df)
        # print()

        return (
            df1[["ParentID", "Rupture Index", "weighted_rate", "solution_id"]]
            .groupby(["ParentID", "Rupture Index", "solution_id"])
            .agg('first')
            .groupby("ParentID")
            .agg('sum')
        )
    '''


"""
TOOD: notes for fault_system_solution participation

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
