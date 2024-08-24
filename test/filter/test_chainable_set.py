import pytest

from solvis.filter.chainable_set_base import ChainableSetBase


class FilterExampleClass(ChainableSetBase):
    """
    An example helper class ...
    """

    def __init__(self, solution):
        self._solution = solution

    def for_example_a(self, _input={1, 2, 3, 4}):
        return self.new_chainable_set(_input, self._solution)

    def for_example_b(self, _input={3, 4, 5, 6}):
        return self.new_chainable_set(_input, self._solution)


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
