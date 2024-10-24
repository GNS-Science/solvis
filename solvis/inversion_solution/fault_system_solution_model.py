"""
This module defines the dataframe models class `FaultSystemSolutionModel`.

FaultSystemSolutionModelprovides methods to build pandas dataframes
from the raw dataframes available via the `InversionSolutionFile` class.
"""
import logging
from typing import TYPE_CHECKING
from .inversion_solution_operations import InversionSolutionOperations as InversionSolutionModel
from .fault_system_solution_file import FaultSystemSolutionFile

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from numpy.typing import NDArray
    # import pandas as pd

    from pandera.typing import DataFrame

    from .dataframe_models import (
        RuptureSectionSchema,
    )


class FaultSystemSolutionModel(InversionSolutionModel):
    """
    For analysis of FaultSystemSolutions
    """

    def __init__(self, solution_file: FaultSystemSolutionFile) -> None:
        self._fast_indices: Optional[pd.DataFrame] = None
        self._solution_file = solution_file
        super().__init__(solution_file)

    @property
    def indices(self):
        return self._solution_file.indices

    @property
    def composite_rates(self):
        return self._solution_file.composite_rates

    @property
    def aggregate_rates(self):
        return self._solution_file.aggregate_rates

    @property
    def rupture_sections(self) -> 'DataFrame[RuptureSectionSchema]':
        if self._fast_indices is None:
            try:
                self._fast_indices = self._solution_file.fast_indices
                log.debug("loaded fast indices")
            except Exception:
                log.info("rupture_sections() building fast indices")
                self._fast_indices = super().build_rupture_sections()
                # TODO: this smells bad ....
                self._solution_file._fast_indices = self._fast_indices

        if self._rupture_sections is None:
            self._rupture_sections = self._fast_indices

        return self._rupture_sections

    def enable_fast_indices(self) -> bool:
        """make sure that the fast_indices dataframe is available at serialisation time"""
        rs = self.rupture_sections  # noqa
        return self._fast_indices is not None
