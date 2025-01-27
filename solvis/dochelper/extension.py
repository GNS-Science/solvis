"""A griffe extension.

Lifted from https://mkdocstrings.github.io/griffe/guide/users/extending/#full-example
"""

import ast
import inspect
from typing import Optional, Union

import griffe

logger = griffe.get_logger(__name__)

logger.setLevel('DEBUG')


class DynamicDocstrings(griffe.Extension):
    """The helper class."""

    def __init__(self, object_paths: Optional[list[str]] = None) -> None:
        self.object_paths = object_paths
        logger.debug(object_paths)
        # assert 0

    def on_instance(
        self,
        node: Union[ast.AST, griffe.ObjectNode],
        obj: griffe.Object,
        agent: Union[griffe.Visitor, griffe.Inspector],
        **kwargs,
    ) -> None:
        logger.info(f'obj {obj} {obj.path}')
        if isinstance(node, griffe.ObjectNode):
            return  # Skip runtime objects, their docstrings are already right.

        def match_path(obj):
            if self.object_paths and obj.path not in self.object_paths:
                for path in self.object_paths:
                    if path in obj.path:
                        return True
                return False
            return True

        if not match_path(obj):
            return

        # Import object to get its evaluated docstring.
        try:
            runtime_obj = griffe.dynamic_import(obj.path)
            docstring = runtime_obj.__doc__
        except ImportError:
            logger.debug(f"Could not get dynamic docstring for {obj.path}")
            return
        except AttributeError:
            logger.debug(f"Object {obj.path} does not have a __doc__ attribute")
            return

        # do not primitive class attributes
        if isinstance(runtime_obj, (str, int, list)):
            return

        # Update the object instance with the evaluated docstring.
        try:
            docstring = inspect.cleandoc(docstring)
            logger.warning(f"evaluated docstring: {docstring}")
        except AttributeError:
            return

        if obj.docstring:
            logger.info(f'obj.docstring {obj.docstring}')
            obj.docstring.value = docstring
        else:
            obj.docstring = griffe.Docstring(
                docstring,
                parent=obj,
                parser=agent.docstring_parser,
                parser_options=agent.docstring_options,
            )
        logger.info(f'updated docstring for {obj.path}: {docstring}')
        # if obj.path == 'solvis.solution.inversion_solution.inversion_solution_file.InversionSolutionFile.RATES_PATH':
        #     ds = griffe.Docstring(
        #         docstring,
        #         parent=obj,
        #         parser=agent.docstring_parser,
        #         parser_options=agent.docstring_options,
        #     )

        #     print(dir(ds))
        #     print(dir(ds.parsed[0]))
        #     print(ds.parsed[0].as_dict())
        #     print(ds.lines)

        #     print()

        #     assert 0
