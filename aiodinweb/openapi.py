"""
OpenAPI Support
~~~~~~~~~~~~~~~

"""
from http import HTTPStatus

import collections

from aiohttp.web_fileresponse import FileResponse
from pathlib import Path
from typing import Dict, Any, Tuple

from .containers import ResourceApi, ApiContainer
from .data_structures import RootPath, EmptyPath
from .exceptions import HttpError
from .operation import Operation
from .web import Request, Response
from .utils import cached_property
from .utils.sequences import dict_filter


class OpenApiSpec(ResourceApi):
    """
    Open API specification.
    """
    name = 'openapi'
    OPENAPI_TAG = '__openapi'
    STATIC_PATH: Path = Path(__file__).parent / 'static-ui'

    def __init__(self, title: str, *,
                 enable_ui: bool=False):
        super().__init__()
        self.title = title

        self.operations.append(Operation(self.openapi_get, EmptyPath, tags=self.OPENAPI_TAG))
        if enable_ui:
            self.operations.append(Operation(self.get_ui, 'ui', tags=self.OPENAPI_TAG))
            self.operations.append(Operation(self.get_static, 'ui/{filename}', tags=self.OPENAPI_TAG))

        self._ui_cache: str = None

    async def openapi_get(self, _: Request) -> Dict[str, Any]:
        """
        Generate OpenAPI specification of attached API.
        """
        api_base = self.parent
        paths, components = self.parse_operations(api_base)
        return dict_filter(
            openapi='3.0.1',
            info={
                'title': self.title,
                'version': str(getattr(api_base, 'version', 0)),
            },
            servers=None,
            paths=paths,
            components=components,
            tags=None,
            externalDocs=None,
        )

    async def get_ui(self, _: Request) -> Response:
        """
        Load the OpenAPI UI.
        """
        if not self._ui_cache:
            content = (STATIC_PATH / 'ui.html').read_text(encoding='UTF-8')
            self._ui_cache = content.replace('{{OPENAPI_PATH}}', '/api/v1/openapi')
        return Response(body=self._ui_cache, content_type='text/html')

    async def get_static(self, request: Request) -> FileResponse:
        """
        Load static content for OpenAPI UI.
        """
        file_name = self.STATIC_PATH / request.match_info['filename']
        content_type = {
            'ss': 'text/css',
            'js': 'application/javascript',
            'ng': 'image/png',
        }.get(file_name[-2:])
        if not (content_type and file_name.exists()):
            raise HttpError(HTTPStatus.NOT_FOUND, 42)

        return FileResponse(file_name, headers={
            'Content-Type': content_type,
            'Content-Encoding': 'gzip',
            'Cache-Control': 'public, max-age=300',
        })

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

        for path, operation in api_base.items():
            # Filter out Open API endpoints
            if self.OPENAPI_TAG in operation.tags:
                continue

            # Cut of first item (will be the parents path)
            path = RootPath / path[1:]

            # Generate a formatted path
            path_spec = paths.setdefault(path.format(), {})

            # Add methods
            for method in operation.methods:
                path_spec[method.lower()] = operation.to_openapi()

        return paths, {}
