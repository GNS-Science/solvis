"""
This module providesa superclass for filter class implementations.

NB: This is used internally, and is not intended for use by solvis API users.

Classes:
 ChainableSetBase: a base class to help making subclass methods chainable & set-like
"""

import copy
from typing import Any, Set, Union

from solvis.solution.typing import SetOperationEnum


class ChainableSetBase:
    """A base class to help making subclass methods chainable & set-like."""

    _chained_set: Set[Any] = set()  # the set

    @property
    def chained_set(self) -> Set[Any]:
        return self._chained_set

    def new_chainable_set(
        self, result, *init_args, join_prior: Union[SetOperationEnum, str] = SetOperationEnum.INTERSECTION
    ) -> 'ChainableSetBase':

        if isinstance(join_prior, str):
            join_prior = SetOperationEnum.__members__[join_prior.upper()]

        instance = self.__class__(*init_args)

        if join_prior == SetOperationEnum.INTERSECTION:
            instance._chained_set = set.intersection(result, self.chained_set) if self.chained_set else result
        elif join_prior == SetOperationEnum.UNION:
            instance._chained_set = set.union(result, self.chained_set) if self.chained_set else result
        elif join_prior == SetOperationEnum.DIFFERENCE:
            instance._chained_set = set.difference(result, self.chained_set) if self.chained_set else result
        elif join_prior == SetOperationEnum.SYMMETRIC_DIFFERENCE:
            instance._chained_set = set.symmetric_difference(result, self.chained_set) if self.chained_set else result
        else:
            raise ValueError(f"Unsupported join type {join_prior}")  # pragma: no cover
        return instance

    def __eq__(self, other) -> bool:
        return other == self.chained_set

    def __iter__(self):
        return self.chained_set.__iter__()

    def __len__(self):
        return self.chained_set.__len__()

    # Set logical operands (&, |, -)

    def __or__(self, *others):
        return self.union(*others)

    def __and__(self, *others):
        return self.intersection(*others)

    def __sub__(self, *others):
        return self.difference(*others)

    def __xor__(self, *other):
        return self.symmetric_difference(*other)

    def __le__(self, *other) -> bool:
        """Test whether every element in the set is in other."""
        return self.issubset(*other)

    def __lt__(self, *other) -> bool:
        """Test whether the set is a proper subset of other.

        That is, set <= other and set != other.
        """
        return self.issubset(*other) and not self.__eq__(*other)

    def __ge__(self, *other) -> bool:
        """Test whether every element in other is in the set."""
        return self.issuperset(*other)

    def __gt__(self, *other) -> bool:
        """Test whether the set is a proper superset of other.

        That is, set >= other and set != other.
        """
        return self.issuperset(*other) and not self.__eq__(*other)

    # Set methods are proxied to the _chained_set ...
    def union(self, *others):
        instance = copy.deepcopy(self)
        instance._chained_set = self.chained_set.union(*others)
        return instance

    def intersection(self, *others):
        instance = copy.deepcopy(self)
        instance._chained_set = self.chained_set.intersection(*others)
        return instance

    def difference(self, *others):
        instance = copy.deepcopy(self)
        instance._chained_set = self.chained_set.difference(*others)
        return instance

    def symmetric_difference(self, *other):
        instance = copy.deepcopy(self)
        instance._chained_set = self.chained_set.symmetric_difference(*other)
        return instance

    def issuperset(self, *others) -> bool:
        return self.chained_set.issuperset(*others)

    def issubset(self, *other) -> bool:
        return self.chained_set.issubset(*other)
