import logging

from aiohttp import web
from http import HTTPStatus
from typing import Union, Callable, Iterable, Tuple, Sequence, Dict

from . import content_type_resolvers
from . import constants
from .data_structures import UrlPath
from .operation import Operation, OperationFunction


class ApiContainer:
    """
    Container for Operations that come together to form an API
    """
    def __init__(self, *children: Union['ApiContainer', Operation],
                 name: str=None, path_prefix: UrlPath.Atoms=None) -> None:
        self.children = list(children)
        self.name = name
        if path_prefix:
            self.path_prefix = UrlPath.parse(path_prefix)
        elif name:
            self.path_prefix = UrlPath.parse(name)
        else:
            self.path_prefix = None

        # Setup this container as children's parent
        for child in children:
            child.parent = self

        self.parent: ApiContainer = None

    def operation(self, path: UrlPath.Atoms, **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Decorate a method as an operation and append to container.
        """
        def inner(func: OperationFunction) -> Operation:
            operation = Operation(func, path, **kwargs)

            # Make operation a child of this container
            self.children.append(operation)
            operation.parent = self

            return operation
        return inner

    def op_paths(self, path_base: UrlPath.Atoms=None) -> Iterable[Tuple[UrlPath, Operation]]:
        """
        Return `URLPath`, `Operation` pairs.
        """
        if path_base:
            path_base = path_base / self.path_prefix
        else:
            path_base = self.path_prefix or UrlPath()

        for child in self.children:
            yield from child.op_paths(path_base)


class ApiCollection(ApiContainer):
    """
    Collection of API endpoints
    """
    parent: ApiContainer = None


class ApiVersion(ApiCollection):
    """
    A specific version of the API
    """
    def __init__(self, *children: Union['ApiContainer', Operation],
                 version: int=1, version_template: str='v{}', **kwargs):
        self.version = version
        self.version_template = version_template
        kwargs.setdefault('name', version_template.format(version))
        super().__init__(*children, **kwargs)


class ApiInterface(ApiContainer):
    """
    Interface between web framework and OdinWeb. This is also always the top
    level of any API tree.
    """
    request_type_resolvers: Sequence[content_type_resolvers.ContentTypeResolver] = (
        content_type_resolvers.accepts_header,
        content_type_resolvers.content_type_header,
        content_type_resolvers.specific_default('application/json')
    )
    """
    Collection of resolvers used to identify the content type of the request.
    """

    response_type_resolvers = [
        content_type_resolvers.accepts_header,
        content_type_resolvers.content_type_header,
        content_type_resolvers.specific_default('application/json'),
    ]
    """
    Collection of resolvers used to identify the content type of the response.
    """

    remap_content_types: Dict[str, str] = {
        'text/plain': 'application/json'
    }
    """
    Remap certain codecs commonly mistakenly used.
    """

    def __init__(self, *children: Union['ApiContainer', Operation],
                 name: str='api', path_prefix: UrlPath.Atoms=None,
                 debug_enabled: bool=False, provide_options: bool=True,
                 logger: logging.Logger=None) -> None:
        """
        :param children: Collection of child containers/operations
        :param name: Name of the API; defaults to "api"
        :param path_prefix: Prefix applied to API path; defaults to "/api"
            (based on the name).
        :param debug_enabled: Enable debug output; this produces a stack trace
            as part of a 500 response.
        :param provide_options: Respond to the Options method automatically.
        :param logger: Logger to log errors to; defaults to builtin.
        """
        self.debug_enabled = debug_enabled
        self.provide_options = provide_options
        self.logger = logger or logging.getLogger(__name__)

        super().__init__(*children, name=name,
                         path_prefix=path_prefix or UrlPath('', name))

        if not self.path_prefix.is_absolute:
            raise ValueError("Path prefix must be an absolute path (eg start with a '/')")

    async def handle_500(self, request: web.Request, exception: Exception) -> web.Response:
        """
        Handle exceptions raised during the processing of a request.

        The default handling is to log the exception (providing the status
        code and request as extra variables) and return an error response.
        """
        self.logger.exception("Unhandled exception during request handling: %s", exception, extra={
            'status_code': HTTPStatus.INTERNAL_SERVER_ERROR,
            'request': request
        })
        return web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, body={
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "code": HTTPStatus.INTERNAL_SERVER_ERROR * 100,
            "message": "Unhandled exception during request handling.",
            "developer_message": None,
            "meta": None
        })

    async def dispatch_operation(self, operation: Operation, request: web.Request):
        """
        Dispatch and handle exceptions from operation.
        """
        try:
            response = await operation(request)

        except NotImplementedError:
            return web.Response(status=HTTPStatus.NOT_IMPLEMENTED, body={
                "status": HTTPStatus.NOT_IMPLEMENTED,
                "code": HTTPStatus.NOT_IMPLEMENTED * 100,
                "message": "The method has not been implemented.",
                "developer_message": None,
                "meta": None
            })

        except Exception as e:
            if self.debug_enabled:
                # If debug is enabled then fallback to the frameworks default
                # error processing, this often provides convenience features
                # to aid in the debugging process.
                raise

            return await self.handle_500(request, e)

        else:
            return response
