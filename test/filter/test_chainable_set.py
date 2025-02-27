import pytest

from solvis.filter.chainable_set_base import ChainableSetBase
from solvis.solution.typing import SetOperationEnum


class FilterExampleClass(ChainableSetBase):
    """
    An example helper class ...
    """

    def __init__(self, solution):
        self._solution = solution

    def for_example_a(self, _input={1, 2, 3, 4}, join_prior: str = 'intersection'):
        return self.new_chainable_set(_input, self._solution, join_prior=join_prior)

    def for_example_b(self, _input={3, 4, 5, 6}, join_prior: str = 'intersection'):
        return self.new_chainable_set(_input, self._solution, join_prior=join_prior)


@pytest.fixture(scope='module')
def filter_example(crustal_solution_fixture):
    yield FilterExampleClass(crustal_solution_fixture)


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

    assert filter_example.for_example_a(SET_A).for_example_b(SET_B, join_prior='intersection') == SET_B.intersection(
        SET_A
    )

    # union
    assert filter_example.for_example_a(SET_A).for_example_b(SET_B, join_prior='union') == SET_B.union(SET_A)

    # difference
    assert filter_example.for_example_a(SET_A).for_example_b(SET_B, join_prior='difference') == SET_B.difference(SET_A)


def test_set_operands(filter_example):
    SET_A = {0, 1, 2, 3}
    SET_B = {1, 2, 3, 4}

    assert filter_example.for_example_a().union(filter_example.for_example_a())

    assert filter_example.for_example_a(SET_A) & filter_example.for_example_a(SET_B) == SET_B.intersection(SET_A)
    assert filter_example.for_example_a(SET_A) | filter_example.for_example_a(SET_B) == SET_B.union(SET_A)
    assert filter_example.for_example_a(SET_A) - filter_example.for_example_a(SET_B) == SET_A.difference(SET_B)


def test_set_proxy_methods_return_class_wrapper(filter_example):

    SET_A = {0, 1, 2, 3}
    SET_B = {1, 2, 3, 4}
    SET_C = {0, 1}

    res0 = filter_example.for_example_a(SET_A)
    res1 = filter_example.for_example_b(SET_B)
    res2 = filter_example.for_example_b(SET_C)

    assert isinstance(res0.intersection(res1), FilterExampleClass)
    assert isinstance(res0.intersection(res1.intersection(res2)), FilterExampleClass)

    assert isinstance(res0 & res1 & res2, FilterExampleClass)
    assert isinstance(res0 | res1 | res2, FilterExampleClass)
    assert isinstance(res0 - res1 - res2, FilterExampleClass)

    # we can't use set.interection without casting
    with pytest.raises(TypeError):
        set.intersection(res0, res1, res2)

    FilterExampleClass.intersection(res0, res1, res2)

    assert isinstance(FilterExampleClass.intersection(res0, res1, res2), FilterExampleClass)
    assert res0 & res1 & res2 == set.intersection(SET_A, SET_B, SET_C)

    assert isinstance(FilterExampleClass.union(res0, res1, res2), FilterExampleClass)
    assert res0 | res1 | res2 == set.union(SET_A, SET_B, SET_C)

    assert isinstance(FilterExampleClass.difference(res0, res1, res2), FilterExampleClass)
    assert res0 - res1 - res2 == set.difference(SET_A, SET_B, SET_C)

    assert isinstance(FilterExampleClass.symmetric_difference(res0, res1), FilterExampleClass)
    assert res0.symmetric_difference(res1) == set.symmetric_difference(SET_A, SET_B)
    assert (res0 ^ res1) == (SET_A ^ SET_B)

    assert isinstance(FilterExampleClass.issubset(res0, res1), bool)
    assert res0.issubset(res1) == SET_A.issubset(SET_B)
    # brackets needed here for operator precedence
    assert (res0 <= res1) == (SET_A <= SET_B)  # __le__()
    assert (res0 < res1) == (SET_A < SET_B)  # __lt__()

    assert isinstance(FilterExampleClass.issuperset(res0, res1), bool)
    assert res0.issuperset(res1) == SET_A.issuperset(SET_B)
    assert (res0 >= res1) == (SET_A >= SET_B)  # __ge__()
    assert (res0 > res1) == (SET_A > SET_B)  # __gt__()

    # TODO there are more set methods to support
    # ref https://docs.python.org/2/library/stdtypes.html#set-types-set-frozenset
