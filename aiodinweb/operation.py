from aiohttp import web
from typing import Callable, Awaitable, Union, Sequence

form . import constants

OperationFunction = Callable[[web.Request, ...], Awaitable[Any]]
Method = Union[str, constants.Method]
Methods = Union[Method, Sequence[Method]]
Empty = tuple()
EmptySet = set()


class Operation:
    """
    Decorator class that wraps API operations
    """
    def __new__(cls, path: str, *, **kwargs):
        def inner(func: OperationFunction):
            instance = super().__new__(cls)
            instance.__init__(func, path, **kwargs)
            return instance
        return inner

    def __init__(self, func: OperationFunction, path: str, *,
                 methods: Methods=constants.Method.GET,
                 tags: Union[str, Sequence[str]]=None,
                 summary: str=None)
        """
        :param func: Function that executes the operation.
        :param path: URL path to the operation.
        :param methods: HTTP method(s) this operation response to.
        """
        self.base_func = self.func = func
        self.path = path
        self.method = force_tuple(method)
        self.tags = set(force_tuple(tags)) if tags else EmptySet
        self.summary = summary
    
    async def __call__(self, request: web.Request, *args, **kwargs) -> Awaitable[Any]:
        return self.func(request, *args, **kwargs)


operation = Operation


def detail(func: OperationFunction=None, *, path: str="{resource_id}", method: Method=constants.Method.GET):
    pass

