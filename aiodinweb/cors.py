from collections import defaultdict
from fnmatch import fnmatch
from typing import Union, Sequence, Type, Dict, Set, Optional

from .constants import Method
from .containers import ApiInterface
from .data_structures import UrlPath
from .middleware import RequestHandler
from .operation import Methods
from .web import Request, Response
from .utils.sequences import dict_filter


class AnyOrigin(object):
    pass


Origins = Union[Sequence[str], Type[AnyOrigin]]


class CORS:
    """
    CORS (Cross-Origin Request Sharing) support for AIOdinWeb APIs.

    This class is designed as a wrapper around an API interface.

    See `MDN documentation <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`_
    for a technical description of CORS.

    :param origins: List of whitelisted origins or use `AnyOrigin` to return a
        '*' or allow all.
    :param max_age: Max length of time access control headers can be cached
        in seconds. `None`, disables this header; a value of -1 will disable
        caching, requiring a pre-flight *OPTIONS* check for all calls.
    :param allow_credentials: Indicate that credentials can be submitted to
        this API.
    :param expose_headers: Request headers can be access by a client beyond
        the simple headers, *Cache-Control*, *Content-Language*,
        *Content-Type*, *Expires*, *Last-Modified*, *Pragma*.
    :param allow_headers: Headers that are allowed to be sent by the browser
        beyond the simple headers, *Accept*, *Accept-Language*,
        *Content-Language*, *Content-Type*.

    """
    priority = 1

    @classmethod
    def apply(cls, api_interface: ApiInterface, origins: Origins, *,
              max_age: int=None, allow_credentials: bool=None,
              expose_headers: Sequence[str]=None, allow_headers: Sequence[str]=None) -> ApiInterface:
        instance = cls(api_interface, origins,
                       max_age=max_age,
                       allow_credentials=allow_credentials,
                       expose_headers=expose_headers,
                       allow_headers=allow_headers)
        api_interface.middleware.append(instance)
        return api_interface

    def __init__(self, api_interface: ApiInterface, origins: Origins, *,
                 max_age: int=None, allow_credentials: bool=None,
                 expose_headers: Sequence[str]=None, allow_headers: Sequence[str]=None) -> None:
        self.origins = origins if origins is AnyOrigin else set(origins)
        self.max_age = max_age
        self.expose_headers = expose_headers
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials

        self._register_options(api_interface)

    def _register_options(self, api_interface: ApiInterface) -> None:
        """
        Register CORS options endpoints.
        """
        # Collapse into a Path->Method dictionary
        paths = defaultdict(set)
        for path, operation in api_interface.items():
            paths[path].update(operation.methods)

        for path, methods in paths.items():
            if Method.Options not in methods:
                self._options_operation(api_interface, path, methods)

    def _options_operation(self, api_interface: ApiInterface, path: UrlPath, methods: Set[Method]) -> None:
        """
        Generate an options operation for the specified path
        """
        # Trim off path prefix.
        if path.startswith(api_interface.path_prefix):
            path = path[len(api_interface.path_prefix):]

        methods.add(Method.Options)

        @api_interface.operation(path, methods=Method.Options,
                                 operation_id=path.format(separator='.') + '.cors_options')
        async def _cors_options(request: Request) -> Response:
            return Response.create(request, headers=self.option_headers(request, methods))

    @staticmethod
    def get_origin(request: Request) -> Optional[str]:
        """
        Get origin from Request.

        This method can be overridden to support HTTP proxies etc.
        """
        return request.headers.get('ORIGIN')

    def match_origin(self, origin: str) -> bool:
        """
        Match against an origin list (allowing for wildcards)
        """
        if origin:
            for pattern in self.origins:
                if fnmatch(origin, pattern):
                    return True
        return False

    def allow_origin(self, request: Request) -> str:
        """
        Generate allow origin header
        """
        if self.origins is AnyOrigin:
            return '*'
        else:
            origin = self.get_origin(request)
            return origin if self.match_origin(origin) else ''

    def option_headers(self, request: Request, methods: Methods) -> Dict[str, str]:
        """
        Generate option headers.
        """
        methods = ', '.join(methods)
        headers = {
            'Allow': methods,
            'Cache-Control': 'no-cache, no-store'
        }

        allow_origin = self.allow_origin(request)
        if allow_origin:
            headers = dict_filter(headers, {
                'Access-Control-Allow-Origin': allow_origin,
                'Access-Control-Allow-Methods': methods,
                'Access-Control-Allow-Credentials': {True: 'true', False: 'false'}.get(self.allow_credentials),
                'Access-Control-Allow-Headers': ', '.join(self.allow_headers) if self.allow_headers else None,
                'Access-Control-Expose-Headers': ', '.join(self.expose_headers) if self.expose_headers else None,
                'Access-Control-Max-Age': str(self.max_age) if self.max_age else None,
            })

        return headers

    async def handle_request(self, request: Request, handler: RequestHandler) -> Response:
        """
        Request handler to allow CORS headers to responses.
        """
        response = await handler(request)

        if request.method != Method.Options:
            response.headers['Access-Control-Allow-Origin'] = self.allow_origin(request)
        return response
