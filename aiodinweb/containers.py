import logging

from aiohttp import web
from http import HTTPStatus
from typing import Union, Callable, Iterable, Tuple, Sequence, Dict

from . import constants
from . import content_type_resolvers
from .data_structures import UrlPath, EmptyPath, Parameter, RootPath
from .operation import Operation, OperationFunction, Methods


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
        'text/plain': 'application/json'
    }
    """
    Remap certain codecs commonly mistakenly used.
    """

    def __init__(self, *children: Union['ApiContainer', Operation],
                 name: str='api', path_prefix: UrlPath.Atoms=RootPath,
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

    async def _dispatch_operation(self, operation: Operation, request: web.Request):
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

    async def _dispatch(self, operation: Operation, request: web.Request) -> web.Response:
        """
        Wrapped dispatch method, prepare request and generate a HTTP Response.
        """
        # Determine the request and response types. Ensure API supports the requested types
        request_type = content_type_resolvers.resolve(self.request_type_resolvers, request)
        request_type = self.remap_content_types.get(request_type, request_type)
        # try:
        #     request.request_codec = self.registered_codecs[request_type]
        # except KeyError:
        #     return HttpResponse.from_status(HTTPStatus.UNPROCESSABLE_ENTITY)

        response_type = content_type_resolvers.resolve(self.response_type_resolvers, request)
        response_type = self.remap_content_types.get(response_type, response_type)
        # try:
        #     request.response_codec = self.registered_codecs[response_type]
        # except KeyError:
        #     return HttpResponse.from_status(HTTPStatus.NOT_ACCEPTABLE)

        # Check if method is in our allowed method list
        if request.method not in operation.methods:
            pass
            # return HttpResponse.from_status(
            #     HTTPStatus.METHOD_NOT_ALLOWED,
            #     {'Allow': ','.join(m.value for m in operation.methods)}
            # )

        # Response types
        resource, status, headers = await self._dispatch_operation(operation, request)

        if isinstance(status, HTTPStatus):
            status = status.value

        # Return a HttpResponse and just send it!
        if isinstance(resource, web.Response):
            return resource

        # Encode the response
        # return create_response(request, resource, status, headers)
        return resource
