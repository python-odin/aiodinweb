"""
OpenAPI Support
~~~~~~~~~~~~~~~

"""
import collections

from typing import Dict, Any, Tuple

from .containers import ApiContainer
from .data_structures import RootPath
from .web import Request
from .utils import cached_property
from .utils.sequences import dict_filter


class OpenApiSpec:
    def __init__(self, title: str):
        self.title = title

    async def __call__(self, request: Request) -> Dict[str, Any]:
        """
        Generate OpenAPI specification of attached API.
        """
        api_base = request.current_operation.parent
        paths, definitions = self.parse_operations(api_base)
        return dict_filter(
            openapi='3.0.1',
            info={
                'title': self.title,
                'version': str(getattr(api_base, 'version', 0)),
            },
            paths=paths,
        )

    @cached_property
    def cenancestor(self) -> ApiContainer:
        """
        Last universal ancestor (or the top level of the API structure).
        """
        ancestor = parent = self.parent
        while parent:
            ancestor = parent
            parent = getattr(parent, 'parent', None)
        return ancestor

    def parse_operations(self, api_base: ApiContainer) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Parse operations into Path -> Method -> Operation structure.

        Will also return definitions of any resources used.
        """
        paths = collections.OrderedDict()

        for path, operation in api_base.op_paths():
            # Filter out Open API endpoints
            if operation.base_func == self:
                continue

            # Cut of first item (will be the parents path)
            path = RootPath / path[1:]

            # Generate a formatted path
            path_spec = paths.setdefault(path.format(), {})

            # Add methods
            for method in operation.methods:
                path_spec[method.lower()] = operation.to_openapi()

        return paths, {}
