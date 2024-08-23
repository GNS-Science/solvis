# from pytest import approx, raises

from typing import Any, Set

import pytest


class ChainableSetBase:
    """A base class to help subclasses filter methods chainable

    And they must also `look like' sets.....

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).

    """

    _chained_set: Set[Any] = set()

    @property
    def chained_set(self):
        return self._chained_set

    def chainable_instance(self, cls, chain_result, *init_args):
        print(f'chainable_instance {cls} {chain_result} {init_args}')
        instance = cls(*init_args)
        instance._chained_set = chain_result
        return instance

    def __example_proxy__(self, *args, **kwargs):
        """methods necessary to behave like a set

        Maybe can use getattr here??
        """
        self._chained_set.__example_proxy__(*args, **kwargs)

    def __eq__(self, other):
        return other == self._chained_set

    def __iter__(self):
        return self._chained_set.__iter__()

    def or_(self, *others):
        return self._chained_set.union(*others)

    def and_(self, *others):
        return self._chained_set.intersection(*others)

    def union(self, *others):
        return self._chained_set.union(*others)

    def intersection(self, *others):
        return self._chained_set.intersection(*others)

    def difference(self, *others):
        return self._chained_set.difference(*others)

    def symmetric_difference(self, other):
        return self._chained_set.symmetric_difference(*other)


class FilterExampleClass(ChainableSetBase):
    """
    An example helper class to filter ruptures, returning the qualifying rupture_ids.

    Class methods all return sets to make it easy to combine filters with
    set operands like `union`, `intersection`, `difference` etc).
    """

    def __init__(self, solution, drop_zero_rates: bool = True):
        """
        Args:
            solution: The solution instance to act on.
            drop_zero_rates: Exclude ruptures with rupture_rate == 0 (default=True)
        """
        self._solution = solution
        super(ChainableSetBase, self).__init__()

    def for_example_a(self, _input={1, 2, 3, 4}) -> Set[int]:
        res = _input
        chained_set = set.intersection(res, self.chained_set) if self.chained_set else res
        return self.chainable_instance(FilterExampleClass, chained_set, self._solution)

    def for_example_b(self, _input={3, 4, 5, 6}) -> Set[int]:
        res = _input
        chained_set = set.intersection(res, self.chained_set) if self.chained_set else res
        return self.chainable_instance(FilterExampleClass, chained_set, self._solution)


@pytest.fixture
def filter_example(fss):
    yield FilterExampleClass(fss)


def test_chaining_a_b(filter_example):
    assert filter_example.for_example_a().chained_set == {1, 2, 3, 4}
    assert filter_example.for_example_b().chained_set == {3, 4, 5, 6}

    assert filter_example.for_example_a().for_example_b().chained_set == {3, 4}

    assert filter_example.chained_set == set()
    assert filter_example.for_example_a({1, 2, 3}).for_example_b({0, 3}).chained_set == {3}


def test_chained_iterable_protocol(filter_example):

    # __iter__
    assert list(filter_example.for_example_a({1, 2, 3})) == [1, 2, 3]

    # __eq__
    assert filter_example.for_example_a({1, 2, 3}).for_example_b({0, 3}) == {3}


def test_chained_set_methods(filter_example):
    # difference
    assert filter_example.for_example_a({1, 2, 3}).difference({1}) == {2, 3}

    # union
    assert filter_example.for_example_a({1, 2, 3}).union({0, 1}) == {0, 1, 2, 3}

    # intersection
    assert filter_example.for_example_a({1, 2, 3}).intersection({0, 1}) == {1}


def test_chained_set_operators(filter_example):
    # it seems tha pythons runtime type-checking won't let us
    # use operarator without the set() wrapping shown below

    # and_ (intersection)
    assert set(filter_example.for_example_a({1, 2, 3})) | {0, 1} == {0, 1, 2, 3}

    # or_ union
    assert set(filter_example.for_example_a({1, 2, 3})) & {0, 1} == {1}
