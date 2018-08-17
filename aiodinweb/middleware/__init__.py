from typing import Callable, Awaitable, Any, Optional, Sequence

from ..web import Request, Response

RequestHandler = Callable[[Request, 'RequestHandler'], Awaitable[Response]]
DispatchHandler = Callable[[Request, 'DispatchHandler'], Awaitable[Any]]
Handle500Handler = Callable[[Request, Exception], Optional[Any]]
OpenApiHandler = Callable[[], Optional[Any]]


class MiddlewareList(list):
    """
    List of middleware with filtering and sorting builtin
    """
    @property
    def request(self) -> Sequence[RequestHandler]:
        """
        List of request middleware methods
        """
        return tuple(m.handle_request for m in self if hasattr(m, 'handle_request'))

    @property
    def dispatch(self) -> Sequence[DispatchHandler]:
        """
        List of dispatch middleware methods.
        """
        return tuple(m.handle_dispatch for m in self if hasattr(m, 'handle_dispatch'))

    @property
    def handle_500(self) -> Sequence[Handle500Handler]:
        """
        List of 500 error handler methods.
        """
        return tuple(m.handle_500 for m in self if hasattr(m, 'handle_500'))

    @property
    def openapi(self) -> Sequence[OpenApiHandler]:
        """
        List of OpenAPI methods.
        """
        return tuple(m.handle_openapi for m in self if hasattr(m, 'handle_openapi'))
