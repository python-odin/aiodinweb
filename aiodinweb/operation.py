from aiohttp import web
from typing import Any, Callable, Awaitable, Union, Sequence, Dict, Set, Iterable, Tuple

from . import constants
from .bases import Request, Response
from .data_structures import Parameter, UrlPath
from .utils.sequences import force_tuple


OperationFunction = Callable[[web.Request, ...], Awaitable[Response]]
Method = Union[str, constants.Method]
Methods = Union[Method, Sequence[Method]]

Empty = tuple()
EmptySet = set()


class Operation:
    """
    Decorator class that wraps API operations
    """
    def __init__(self, func: OperationFunction, path: UrlPath.Atoms, *,
                 methods: Methods=constants.Method.Get,
                 tags: Union[str, Sequence[str]]=None,
                 summary: str=None,
                 description: str=None,
                 operation_id: str=None,
                 deprecated: bool = False
                 ) -> None:
        """
        :param func: Function that executes the operation.
        :param path: URL path to the operation.
        :param methods: HTTP method(s) this operation response to.
        """
        self.base_func = self.func = func
        self.path = UrlPath.parse(path)
        self.methods = force_tuple(methods)
        self.tags = set(force_tuple(tags)) if tags else EmptySet
        self.summary = summary
        self.description = description or func.__doc__
        self.operation_id = operation_id or func.__name__
        self.deprecated = deprecated

        self.parameters: Set[Parameter] = set()
        self.request_body = None
        self.responses: Dict[int, Any] = None
        self.security = None

        self.parent = None

    async def __call__(self, request: Request, *args, **kwargs) -> Awaitable[Response]:
        return self.func(request, *args, **kwargs)

    def op_paths(self, path_base: UrlPath.Atoms=None) -> Iterable[Tuple[UrlPath, 'Operation']]:
        """
        Return `URLPath`, `Operation` pairs.
        """
        url_path = self.path
        if path_base:
            url_path = path_base / url_path
        yield url_path, self
