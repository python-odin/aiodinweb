import logging
import json

from aiohttp.web import Application, RouteDef, route
from functools import partial
from http import HTTPStatus
from typing import Union, Callable, Iterable, Tuple, Sequence, Dict, Any, Optional

from . import constants
from . import content_type_resolvers
from .data_structures import UrlPath, EmptyPath, Parameter, RootPath, MiddlewareList
from .exceptions import ImmediateHttpResponse
from .resources import Error
from .operation import Operation, OperationFunction, Methods
from .web import Request, Response

CODECS = {
    'application/json': json,
}


class ApiContainer:
    """
    Container for Operations that come together to form an API
    """
    def __init__(self, *children: Union['ApiContainer', Operation],
                 name: str=None, path_prefix: UrlPath.Atoms=None) -> None:
        self.children = list(children)
        self.name = name
        if path_prefix:
            self.path_prefix = UrlPath.from_object(path_prefix)
        elif name:
            self.path_prefix = UrlPath.parse(name)
        else:
            self.path_prefix = EmptyPath

        # Setup this container as children's parent
        for child in children:
            child.parent = self

        self.parent: ApiContainer = None

    def _decorator(self, func: OperationFunction, path: UrlPath.Atoms,
                   **kwargs) -> Callable[[OperationFunction], Operation]:
        def inner(f: OperationFunction) -> Operation:
            operation = Operation(f, path, **kwargs)
            self.children.append(operation)
            operation.parent = self
            return operation
        return inner(func) if func else inner

    def operation(self, path: UrlPath.Atoms, **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Decorate a method as an operation and append to container.
        """
        return self._decorator(path=path, **kwargs)

    def listing(self, func: OperationFunction=None, *,
                path: UrlPath.Atoms=EmptyPath,
                **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Listing operation
        """
        return self._decorator(func, path, **kwargs)

    def create(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms=EmptyPath,
               methods: Methods = constants.Method.Post,
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Create operation
        """
        kwargs['methods'] = methods
        return self._decorator(func, path, **kwargs)

    def detail(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path)),
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Detail operation
        """
        return self._decorator(func, path, **kwargs)

    def update(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path)),
               methods: Methods = constants.Method.Put,
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Update operation
        """
        kwargs['methods'] = methods
        return self._decorator(func, path, **kwargs)

    def delete(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path)),
               methods: Methods = constants.Method.Delete,
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Delete operation
        """
        kwargs['methods'] = methods
        return self._decorator(func, path, **kwargs)

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
        'text/plain': 'application/json',
        'text/javascript': 'application/json',
        'text/x-javascript': 'application/json',
        'text/x-json': 'application/json',
        'application/x-javascript': 'application/json',
        # This is a common default content type.
        'application/octet-stream': 'application/json',
    }
    """
    Remap certain codecs commonly mistakenly used.
    """

    registered_codecs = CODECS
    """
    Codecs that are supported by this API.
    """

    def __init__(self, *children: Union['ApiContainer', Operation],
                 name: str='api', path_prefix: UrlPath.Atoms=None,
                 debug_enabled: bool=False, provide_options: bool=True,
                 middleware: list=None, logger: logging.Logger=None) -> None:
        """
        :param children: Collection of child containers/operations
        :param name: Name of the API; defaults to "api"
        :param path_prefix: Prefix applied to API path; defaults to "/api"
            (based on the name).
        :param debug_enabled: Enable debug output; this produces a stack trace
            as part of a 500 response.
        :param provide_options: Respond to the Options method automatically.
        :param middleware: List of middleware
        :param logger: Logger to log errors to; defaults to builtin.
        """
        self.debug_enabled = debug_enabled
        self.provide_options = provide_options
        self.middleware = MiddlewareList(middleware or [])
        self.logger = logger or logging.getLogger(__name__)

        super().__init__(*children, name=name, path_prefix=path_prefix or UrlPath('', name))

        if not self.path_prefix.is_absolute:
            raise ValueError("Path prefix must be an absolute path (eg start with a '/')")

    async def handle_500(self, request: Request, exception: Exception) \
            -> Tuple[Any, Optional[HTTPStatus], Optional[Dict[str, str]]]:
        """
        Handle exceptions raised during the processing of a request.

        The default handling is to log the exception (providing the status
        code and request as extra variables) and return an error response.
        """
        # Let middleware attempt to handle exception
        try:
            for middleware in self.middleware.handle_500:
                response = middleware(request, exception)
                if response:
                    return response

        except Exception as ex:
            exception = ex

        # Fallback to generic error
        self.logger.exception(
            "Unhandled exception during request handling: %s", exception,
            extra={'status': HTTPStatus.INTERNAL_SERVER_ERROR, 'request': request}
        )

        return (
            Error.from_status(HTTPStatus.INTERNAL_SERVER_ERROR),
            HTTPStatus.INTERNAL_SERVER_ERROR, None
        )

    async def _dispatch_operation(self, request: Request, operation: Operation) \
            -> Tuple[Any, Optional[HTTPStatus], Optional[Dict[str, str]]]:
        """
        Dispatch and handle exceptions from operation.
        """
        try:
            # Apply dispatch middleware
            handler = operation
            for middleware in self.middleware.dispatch:
                handler = partial(middleware, handler=handler)

            resource = await handler(request)

        except ImmediateHttpResponse as e:
            # An exception used to return a response immediately, skipping any
            # further processing.
            return e.resource, e.status, e.headers

        except NotImplementedError:
            resource = Error.from_status(HTTPStatus.NOT_IMPLEMENTED)
            return resource, HTTPStatus.NOT_IMPLEMENTED, None

        except Exception as ex:
            if self.debug_enabled:
                # If debug is enabled then fallback to the frameworks default
                # error processing, this often provides convenience features
                # to aid in the debugging process.
                raise

            return await self.handle_500(request, ex)

        else:
            return resource, None, None

    async def _dispatch(self, request: Request, operation: Operation) -> Response:
        """
        Wrapped dispatch method, prepare request and generate a HTTP Response.
        """
        # Determine the request and response types. Ensure API supports the requested types
        request_type = content_type_resolvers.resolve(self.request_type_resolvers, request)
        request_type = self.remap_content_types.get(request_type, request_type)
        try:
            request.request_codec = self.registered_codecs[request_type]
            request.request_codec.content_type = request_type
        except KeyError:
            return Response.from_status(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                reason="Unknown request content-type",
            )

        response_type = content_type_resolvers.resolve(self.response_type_resolvers, request)
        response_type = self.remap_content_types.get(response_type, response_type)
        try:
            request.response_codec = self.registered_codecs[response_type]
            request.response_codec.content_type = response_type
        except KeyError:
            return Response.from_status(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                reason="Unknown response content-type",
            )

        # Check if method is in our allowed method list
        if request.method not in operation.methods:
            return Response.from_status(
                HTTPStatus.METHOD_NOT_ALLOWED,
                headers={
                    'Allow': ','.join(m.value for m in operation.methods)
                }
            )

        # Response types
        resource, status, headers = await self._dispatch_operation(request, operation)

        # Return a HttpResponse and just send it!
        if isinstance(resource, Response):
            return resource

        # Encode the response
        return Response.create(request, resource, status, headers)

    async def dispatch(self, operation: Operation, request: Request) -> Response:
        """
        Dispatch incoming request and capture top level exceptions.
        """
        request.current_operation = operation

        try:
            # Apply request middleware
            handler = partial(self._dispatch, operation=operation)
            for middleware in self.middleware.dispatch:
                handler = partial(middleware, handler=handler)

            response = await handler(request)

        except Exception as ex:
            if self.debug_enabled:
                # If debug is enabled then fallback to the frameworks default
                # error processing, this often provides convenience features
                # to aid in the debugging process.
                raise

            resource, status, headers = await self.handle_500(request, ex)
            return Response.create(request, resource, status, headers)

        else:
            return response


class AioApi(ApiInterface):
    """
    API Interface for AIO-HTTP
    """
    def _bound_callback(self, operation: Operation):
        async def callback(request: Request) -> Response:
            return await self.dispatch(operation, request)
        return callback

    def _routes(self) -> Iterable[RouteDef]:
        for url_path, operation in self.op_paths():
            for method in operation.methods:
                yield route(method, url_path.format(), self._bound_callback(operation))

    def add_routes(self, app: Application) -> None:
        """
        Setup routes
        """
        app.add_routes(self._routes())
