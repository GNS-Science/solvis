import pytest

from solvis.filter.chainable_set_base import ChainableSetBase
from solvis.inversion_solution.typing import SetOperationEnum


class FilterExampleClass(ChainableSetBase):
    """
    An example helper class ...
    """

    def __init__(self, solution):
        self._solution = solution

    def for_example_a(self, _input={1, 2, 3, 4}):
        return self.new_chainable_set(_input, self._solution)

    def for_example_b(self, _input={3, 4, 5, 6}, join_prior: SetOperationEnum = SetOperationEnum.INTERSECTION):
        return self.new_chainable_set(_input, self._solution, join_prior=join_prior)


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

    # __iter__ method supported
    assert list(filter_example.for_example_a({1, 2, 3})) == [1, 2, 3]

    # __eq__ method supported
    assert filter_example.for_example_a({1, 2, 3}).for_example_b({0, 3}) == {3}


def test_chained_set_methods(filter_example):

    # difference
    assert filter_example.for_example_a({1, 2, 3}).difference({1}) == {2, 3}

    # union
    assert filter_example.for_example_a({1, 2, 3}).union({0, 1}) == {0, 1, 2, 3}

    # intersection
    assert filter_example.for_example_a({1, 2, 3}).intersection({0, 1}) == {1}


def test_chained_set_operators(filter_example):
    # pythons runtime type-checking won't let us
    # use operands (&,|,+) without set() wrapping shown below

    # and_ (intersection)
    assert set(filter_example.for_example_a({1, 2, 3})) | {0, 1} == {0, 1, 2, 3}

    # or_ union
    assert set(filter_example.for_example_a({1, 2, 3})) & {0, 1} == {1}


@pytest.mark.review
def test_chained_set_join_types(filter_example):

    # difference
    SET_A = {0, 1, 2, 3}
    SET_B = {1, 2, 3, 4}

    # default == intersection
    assert filter_example.for_example_a(SET_A).for_example_b(SET_B) == SET_A.intersection(SET_B)

    # intersection
    assert filter_example.for_example_a(SET_A).for_example_b(
        SET_B, join_prior=SetOperationEnum.INTERSECTION
    ) == SET_B.intersection(SET_A)

    # union
    assert filter_example.for_example_a(SET_A).for_example_b(SET_B, join_prior=SetOperationEnum.UNION) == SET_B.union(
        SET_A
    )

    # difference
    assert filter_example.for_example_a(SET_A).for_example_b(
        SET_B, join_prior=SetOperationEnum.DIFFERENCE
    ) == SET_B.difference(SET_A)
