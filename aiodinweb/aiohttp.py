from aiohttp.web import Application, RouteDef, route

from typing import Generator, Awaitable

from . import api
from .containers import ApiInterface
from .operation import Operation


class AioApiInterface(ApiInterface):
    """
    API Interface for AIO-HTTP
    """
    def _bound_callback(self, operation: Operation):
        async def callback(request: api.Request) -> api.Response:
            return await self._dispatch(operation, request)
        return callback

    def _routes(self) -> Generator[RouteDef, None, None]:
        for url_path, operation in self.op_paths():
            for method in operation.methods:
                yield route(method, url_path.format(), self._bound_callback(operation))

    def setup(self, app: Application) -> None:
        """
        Setup routes
        """
        app.add_routes(self._routes())
