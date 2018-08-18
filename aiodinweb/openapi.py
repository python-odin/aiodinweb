"""
OpenAPI Support
~~~~~~~~~~~~~~~

"""
import collections

from aiohttp.web_fileresponse import FileResponse
from http import HTTPStatus
from itertools import chain
from pathlib import Path
from typing import Dict, Any, List, NamedTuple, Sequence

from .containers import ResourceApi, ApiContainer
from .data_structures import RootPath, EmptyPath, UrlPath
from .exceptions import HttpError
from .operation import Operation
from .resources import Error
from .web import Request, Response
from .utils import cached_property
from .utils.sequences import dict_filter
from .json_schema import resource_schema


class Server(NamedTuple):
    """
    Definition of a server, the url may contain a single %(host)s to represent
    the current host.

    This definition does not support OpenAPI 3.0.1 template URLs. % formatting
    is used however to allow for {} style templates in the future.
    """
    base_url: str
    description: str = None


class OpenApiSpec(ResourceApi):
    """
    Open API specification.

    :param title: Title of the OpenAPI spec.
    :param description: Description of the OpenAPI spec.
    :param name: Name of the URL, this is used in the URL; default is
        `openapi`.
    :param additional_servers: List of additional locations that serves this
        API.
    :param host: Override identified host, useful for reverse proxies.
    :param enable_ui: Enable Swagger UI. This will enable both serving of the
        Swagger UI HTML as well as static content required to enable it. The
        default build uses the interface provided by
        `swagger.io <https://swagger.io>`_. You can customise the swagger UI
        by providing an alternate `static_path` to your own version. This
        defaults to `False` and must be explicitly enabled.
    :param static_path: An alternative location for the Swagger UI static
        files. All files (except the HTML template) should be gzipped as files
        are served as if they are GZip encoded.
    """
    OPENAPI_TAG = '__openapi'

    base_servers: Sequence[Server] = [Server('%(host)s%(base)s', 'Current host')]

    def __init__(self, title: str, *,
                 description: str=None,
                 additional_servers: Sequence[Server]=None,
                 host: str=None,
                 name: str='openapi',
                 enable_ui: bool=False,
                 static_path: Path=Path(__file__).parent / 'static-ui'):
        self.name = name
        super().__init__()

        self.title = title
        self.description = description
        self.additional_servers = additional_servers
        self.host = host
        self.static_path = static_path

        # Configure operations
        self.operations.append(Operation(self.openapi_get, EmptyPath, tags=self.OPENAPI_TAG))
        if enable_ui:
            self.operations.append(Operation(self.get_ui, 'ui', tags=self.OPENAPI_TAG))
            self.operations.append(Operation(self.get_static, 'ui/{filename}', tags=self.OPENAPI_TAG))

        self._ui_cache: str = None

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

    @cached_property
    def base_path(self) -> UrlPath:
        """
        Calculate the APIs base path
        """
        path = UrlPath()

        # Walk up the API to find the base object
        parent = self.parent
        while parent:
            path_prefix = getattr(parent, 'path_prefix', EmptyPath)
            path = path_prefix / path
            parent = getattr(parent, 'parent', None)

        return path

    @cached_property
    def api_path(self) -> UrlPath:
        """
        Path to the OpenAPI spec
        """
        return self.base_path / self.name

    def parse_operations(self):
        """
        Generate OpenAPI paths and components list.

        Parse operations into Path -> Method -> Operation structure.

        """
        resources = {Error}

        paths = collections.OrderedDict()
        for path, operation in self.parent.items():
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

            # Add parameters
            if path.parameters:
                path_spec['parameters'] = [p.to_openapi() for p in path.parameters]

        return (
            paths,
            dict(resource_schema(r) for r in resources)
        )

    def servers_spec(self, request: Request) -> List[Dict[str, Any]]:
        """
        Generate OpenAPI servers list
        """
        host = self.host
        if not host:
            # Determine the host from the current request
            host = f'{request.scheme}://{request.host}'
        format_dict = {'host': host, 'base': self.base_path}

        # Convert into dictionaries and apply formatting.
        return [
            {'url': (s.base_url % format_dict), 'description': s.description}
            for s in chain(self.base_servers, self.additional_servers or [])
        ]

    def security_schemes(self) -> Dict[str, List[str]]:
        """
        Generate OpenAPI security schemes.
        """

    async def openapi_get(self, request: Request) -> Dict[str, Any]:
        """
        Generate OpenAPI specification of attached API.
        """
        paths, schema_defs = self.parse_operations()

        return dict_filter(
            openapi='3.0.1',
            info=dict_filter(
                title=self.title,
                description=self.description,
                version=getattr(self.parent, 'version', 0),
            ),
            servers=self.servers_spec(request),
            paths=paths,
            components=dict_filter(
                schemas=schema_defs,
                responses=None,
                parameters=None,
            ),
            security=self.security_schemes(),
        )

    async def get_ui(self, _: Request) -> Response:
        """
        Load the OpenAPI UI.

        The HTML is cached in memory
        """
        if not self._ui_cache:
            content = (self.static_path / 'ui.html').read_text(encoding='UTF-8')
            self._ui_cache = content.replace('{{OPENAPI_PATH}}', str(self.api_path))
        return Response(body=self._ui_cache, content_type='text/html')

    async def get_static(self, request: Request) -> FileResponse:
        """
        Load static content for OpenAPI UI.
        """
        file_name = request.match_info['filename']

        # Check file exists and is a known content type.
        content_type = {
            'ss': 'text/css',
            'js': 'application/javascript',
            'ng': 'image/png',
        }.get(file_name[-2:])
        file_path = self.static_path / file_name
        if not (content_type and file_path.exists()):
            raise HttpError(HTTPStatus.NOT_FOUND, 42)

        return FileResponse(file_path, headers={
            'Content-Type': content_type,
            'Content-Encoding': 'gzip',  # Content is pre-gzipped
            'Cache-Control': 'public, max-age=300',
        })
