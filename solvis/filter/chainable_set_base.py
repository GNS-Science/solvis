"""

"""
from typing import Any, Set


class ChainableSetBase:
    """A base class to make subclasse filter methods chainable & set-like"""

    _chained_set: Set[Any] = set()

    @property
    def chained_set(self) -> Set[Any]:
        return self._chained_set

    def new_chainable_set(self, result, *init_args):
        instance = self.__class__(*init_args)
        instance._chained_set = set.intersection(result, self.chained_set) if self.chained_set else result
        return instance

    def __eq__(self, other):
        return other == self.chained_set

    def __iter__(self):
        return self.chained_set.__iter__()

    def __len__(self):
        return self.chained_set.__len__()

    # Set methods are proxied to the _chained_set ...

    def or_(self, *others):
        return self.chained_set.union(*others)

    def and_(self, *others):
        return self.chained_set.intersection(*others)

    def union(self, *others):
        return self.chained_set.union(*others)

    def intersection(self, *others):
        return self.chained_set.intersection(*others)

    def difference(self, *others):
        return self.chained_set.difference(*others)

    def symmetric_difference(self, other):
        return self.chained_set.symmetric_difference(*other)

    def issuperset(self, *others):
        return self.chained_set.issuperset(*others)

    def issubset(self, other):
        return self.chained_set.issubset(other)
