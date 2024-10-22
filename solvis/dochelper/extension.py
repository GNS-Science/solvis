"""
A griffe extension lifted from https://mkdocstrings.github.io/griffe/guide/users/extending/#full-example


"""
import ast
import inspect
import griffe

from typing import Union, Optional
logger = griffe.get_logger(__name__)

logger.setLevel('DEBUG')

class DynamicDocstrings(griffe.Extension):

    def __init__(self, object_paths: Optional[list[str]] = None) -> None:
        self.object_paths = object_paths

    def on_instance(
        self,
        node: Union[ast.AST, griffe.ObjectNode],
        obj: griffe.Object,
        agent: Union[griffe.Visitor, griffe.Inspector],
        **kwargs,
    ) -> None:
        logger.debug(f'obj {obj} {obj.path}')
        if isinstance(node, griffe.ObjectNode):
            return  # Skip runtime objects, their docstrings are already right.

        if self.object_paths and obj.path not in self.object_paths:
            for path in self.object_paths:
                if path not in obj.path:
                    return  # Skip objects that were not selected.

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

        # Update the object instance with the evaluated docstring.
        try:
            docstring = inspect.cleandoc(docstring)
        except AttributeError:
            return

        if obj.docstring:
            obj.docstring.value = docstring
        else:
            obj.docstring = griffe.Docstring(
                docstring,
                parent=obj,
                parser=agent.docstring_parser,
                parser_options=agent.docstring_options,
            )
        logger.warning(f'updated docstring for {obj.path}: {docstring}')
