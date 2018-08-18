import logging

from aiohttp.web import Application, StreamResponse
from functools import partial
from http import HTTPStatus
from odin.codecs import json_codec
from operator import attrgetter
from typing import Union, Callable, Iterable, Tuple, Sequence, Dict, Any, Optional, List

from . import constants
from . import content_type_resolvers
from .data_structures import UrlPath, EmptyPath, Parameter
from .exceptions import ImmediateHttpResponse
from .middleware import MiddlewareList
from .resources import Error
from .operation import Operation, OperationFunction, Methods
from .web import Request, Response

CODECS = {
    'application/json': json_codec,
}


class ResourceApiType(type):
    """
    Meta class that resolves operations to routes.
    """
    def __new__(mcs, name: str, bases: Sequence[type], attrs: Dict[str, Any]) -> 'ResourceApiType':
        super_new = super().__new__

        if name == 'NewBase' and attrs == {}:
            return super_new(mcs, name, bases, attrs)

        parents = [
            b for b in bases
            if isinstance(b, ResourceApiType) and not (b.__name__ == 'NewBase' and b.__mro__ == (b, object))
        ]
        if not parents:
            # If this isn't a subclass of don't do anything special.
            return super_new(mcs, name, bases, attrs)

        # Determine the resource used by this API (handle inherited resources)
        api_resource = attrs.get('resource')
        if api_resource is None:
            for base in bases:
                api_resource = getattr(base, 'resource')
                if api_resource:
                    break

        new_class = super_new(mcs, name, bases, attrs)

        # Get operations
        operations = []
        for obj in attrs.values():
            if isinstance(obj, Operation):
                operations.append(obj)
                obj.bind_to_instance(new_class)

        # Get routes from parent objects
        for parent in parents:
            parent_operations = getattr(parent, '_operations', None)
            if parent_operations:
                operations.extend(parent_operations)

        # Populate operations
        new_class.operations = sorted(operations, key=attrgetter('sort_key'))

        return new_class


class ResourceApi(metaclass=ResourceApiType):
    """
    Base class for APIs that manage a particular resource type.
    """
    name: str = None
    """
    Name of the API resource
    """

    resource = None
    """
    The Odin resource this API is modelled on.
    """

    path_prefix: UrlPath = EmptyPath
    """
    Prefix to prepend to any generated path.
    """

    parent: 'ApiContainer' = None
    """
    Parent API container
    """

    operations: List[Operation] = None
    """
    Operations added to this api. This is populated by Metaclass
    """

    def __init__(self):
        if not self.name:
            self.name = None

        # Append APIs name to path prefix
        self.path_prefix /= self.name

    def items(self, path_base: UrlPath.Atoms=None) -> Iterable[Tuple[UrlPath, Operation]]:
        """
        Return `URLPath`, `Operation` pairs.
        """
        if path_base:
            path_base = path_base / self.path_prefix
        else:
            path_base = self.path_prefix or UrlPath()

        for operation in self.operations:
            yield from operation.items(path_base)


class ApiContainer:
    """
    Container for Operations that come together to form an API
    """
    def __init__(self, *children: Union['ApiContainer', Operation, ResourceApi],
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
        return self._decorator(None, path, **kwargs)

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
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path,
                                                       data_type=constants.DataType.String)),
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Detail operation
        """
        return self._decorator(func, path, **kwargs)

    def update(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path,
                                                       data_type=constants.DataType.String)),
               methods: Methods = constants.Method.Put,
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Update operation
        """
        kwargs['methods'] = methods
        return self._decorator(func, path, **kwargs)

    def delete(self, func: OperationFunction=None, *,
               path: UrlPath.Atoms = UrlPath(Parameter('resource_id', constants.In.Path,
                                                       data_type=constants.DataType.String)),
               methods: Methods = constants.Method.Delete,
               **kwargs) -> Callable[[OperationFunction], Operation]:
        """
        Delete operation
        """
        kwargs['methods'] = methods
        return self._decorator(func, path, **kwargs)

    def items(self, path_base: UrlPath.Atoms=None) -> Iterable[Tuple[UrlPath, Operation]]:
        """
        Return `URLPath`, `Operation` pairs.
        """
        if path_base:
            path_base = path_base / self.path_prefix
        else:
            path_base = self.path_prefix or UrlPath()

        for child in self.children:
            yield from child.items(path_base)


class ApiCollection(ApiContainer):
    """
    Collection of API endpoints
    """
    parent: ApiContainer = None


class ApiVersion(ApiCollection):
    """
    A specific version of the API
    """
    def __init__(self, *children: Union['ApiContainer', Operation, ResourceApi],
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

    async def _dispatch(self, request: Request, operation: Operation) -> StreamResponse:
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
        if isinstance(resource, StreamResponse):
            return resource

        # Encode the response
        return Response.create(request, resource, status, headers)

    async def dispatch(self, operation: Operation, request: Request) -> StreamResponse:
        """
        Dispatch incoming request and capture top level exceptions.
        """
        request.current_operation = operation

        try:
            # Apply request middleware
            handler = partial(self._dispatch, operation=operation)
            for middleware in self.middleware.request:
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
    def _bound_operation(self, operation: Operation):
        async def bound_operation(request: Request) -> StreamResponse:
            return await self.dispatch(operation, request)
        return bound_operation

    @staticmethod
    def _parameter_formatter(parameter: Parameter) -> str:
        """
        Format a parameter to be consumable by the `UrlPath.parse`.
        """
        return f"{{{parameter.name}}}"

    def add_routes(self, app: Application) -> None:
        """
        Setup routes
        """
        router = app.router
        for url_path, operation in self.items():
            for method in operation.methods:
                router.add_route(
                    method, url_path.format(self._parameter_formatter),
                    self._bound_operation(operation)
                )
