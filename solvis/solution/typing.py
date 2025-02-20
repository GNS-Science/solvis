"""This module defines type classes for the `inversion_solution` package."""

from enum import Enum
from typing import Any, List, Optional, Protocol


class ModelLogicTreeBranch(Protocol):
    """A protocol class representing a branch in the model logic tree.

    Attributes:
        values: A list of values associated with the branch.
        weight: The weight of the branch in the logic tree.
        onfault_nrml_id: An optional string identifier for the on-fault branch.
        distributed_nrml_id: An optional string identifier for the distributed branch.
        inversion_solution_id: An optional string identifier for the inversion solution.
        inversion_solution_type: An optional string specifying the type of inversion solution.
    """

    values: List[Any]
    weight: float
    onfault_nrml_id: Optional[str] = ""
    distributed_nrml_id: Optional[str] = ""
    inversion_solution_id: Optional[str] = ""
    inversion_solution_type: Optional[str] = ""


class SetOperationEnum(Enum):
    """Enumerated type for common set operations.

    Attributes:
        UNION (int): Represents the union operation.
        INTERSECTION (int): Represents the intersection operation.
        DIFFERENCE (int): Represents the difference operation.
        SYMMETRIC_DIFFERENCE (int): Represents the symmetric difference operation.
    """

    UNION = 1
    INTERSECTION = 2
    DIFFERENCE = 3
    SYMMETRIC_DIFFERENCE = 4
