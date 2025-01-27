# import copy
from inspect import getmembers, isfunction


def inherit_docstrings(cls):
    """A decorator function hoisting docstrings from superclass methods

    taken from: https://stackoverflow.com/a/17393254
    see also: https://github.com/rcmdnk/inherit-docstring for a pypi package
    """

    def docstrings_for(o: object):
        # print(o)
        if isinstance(o, property):
            return True
        elif isfunction(o):
            return True
        else:
            return False

    for name, method in getmembers(cls, docstrings_for):
        if method.__doc__:
            continue
        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                method.__doc__ = getattr(parent, name).__doc__
                continue
    return cls
