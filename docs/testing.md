# Testing

If you would like to contribute to the project, [poetry][] is
recommended for creating and managing a local development
environment. In order to get all of the tests running,
[install](installation.md) with all extras:

```
poetry install --all-extras
```

Solvis uses [pytest][] and [tox][] to test its code.

Pytest is used to run the unit tests, found in the `test/` directory.

Tox creates and manages virtual environments to support testing across
multiple versions of Python, as well as running other build and code
quality tools.

For code quality, the following tools are used:

* **black** and **flake8** for linting
* **isort** for file import tidying
* **mypy** for static type checking


## pytest
By default, pytest will search for all tests in the `test/` directory.
Tests can be run for a single file:
```console
$ poetry run pytest test/geometry/test_geometry.py
```

Specific tests can also be specified by their class and function name:
``` console
$ poetry run pytest test/geometry/test_circle_polygon.py::TestCirclePoly::test_no_negative_lats_in_circle_polygon
```

Or filtered by keywords (this runs two tests in separate files):
``` console
$ poetry run pytest -k no_negative_lats
```

Be aware that there may be a number of warnings from upstream
dependencies such as Pandas and NumPy. These should hopefully be
removed as and when dependency versions can be upgraded.

**Note**:
 when working on a bug or feature it is fine to run tests by themselves,
but it is recommended to run the full test suite before submitting code
to ensure there are no unexpected interactions with other parts of the
codebase.

## tox
Tox builds a number of isolated environments to support testing of
the library across multiple versions of Python.

**Note**: Tox will only test for the versions of Python that you have
installed. If you wish to test across all supported environments, you
will need to install each supported minor release. Consider using a
tool like [pyenv][] to manage multiple concurrent Python version
installs.

To run all tox environments:
```console
$ poetry run tox
```

For one or more specific environments (e.g. formatting and linting):
```console
$ poetry run tox -e format -e lint
```

### Code coverage

Running any of the Python version test environments will also generate
code coverage reports (`.coverage` and `coverage.xml`) for use in
text editors that support them. Only a single test environment is
required:

```console
$ poetry run tox -e py311

...

$ ls -1a | grep coverage
.coverage
coverage.xml
```


## Cleaning up temporary files

Some of these tools create temporary files/environments to speed up the
process of running tests. These take up extra space, so once development
work is done you may wish to remove the following directories:

* `.mypy_cache`
* `.pytest_cache`
* `.tox`

Or all non-committed files and directories at once with:

```console
$ git clean -dfx
```


[poetry]: https://python-poetry.org/
[pyenv]: https://github.com/pyenv/pyenv
[pytest]: https://docs.pytest.org/en/stable/
[tox]: https://tox.wiki/