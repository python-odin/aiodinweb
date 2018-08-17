from functools import partial

from aiohttp import web
from typing import Callable, Awaitable, Union, Sequence, Set, Iterable, Tuple, Dict, Any

from aiodinweb.utils import cached_property
from . import constants
from .data_structures import Parameter, UrlPath, MiddlewareList
from .utils.sequences import force_tuple, dict_filter
from .web import Request, Response


OperationFunction = Callable[[web.Request], Awaitable[Response]]
Method = Union[str, constants.Method]
Methods = Union[Method, Sequence[Method]]

Empty = tuple()
EmptySet = set()


class Operation:
    """
    Decorator class that wraps API operations
    """
    _operation_count = 0

    def __init__(self, func: OperationFunction, path: UrlPath.Atoms, *,
                 methods: Methods=constants.Method.Get,
                 tags: Union[str, Sequence[str]]=None,
                 summary: str=None,
                 middleware: Sequence[object]=None) -> None:
        """
        :param func: Function that executes the operation.
        :param path: URL path to the operation.
        :param methods: HTTP method(s) this operation response to.
        """
        self.base_func = self.func = func
        self._path = UrlPath.from_object(path)
        self.methods = force_tuple(methods)

        # Sorting/hashing
        self.sort_key = Operation._operation_count
        Operation._operation_count += 1

        # Parent object (when associated with an API Container)
        self.parent = None
        # Binding when part of an API class
        self.binding = None

        self.middleware = MiddlewareList(middleware or [])
        self.middleware.append(self)  # Add self as middleware to obtain pre-dispatch support

        # Security
        self.security = None

        # Documentation
        self._tags = set(force_tuple(tags)) if tags else EmptySet
        self.summary = summary
        self.deprecated = False
        self.parameters: Set[Parameter] = set()

        # Copy values from function (if defined)
        for attr in ('deprecated', 'parameters', 'security'):
            try:
                value = getattr(func, attr)
            except AttributeError:
                pass
            else:
                setattr(self, attr, value)

    async def __call__(self, request: Request) -> Response:
        """
        Main wrapper around the operation function.
        """
        # Apply middleware
        handler = self.func
        for middleware in self.middleware.dispatch:
            handler = partial(middleware, handler=handler)

        return await handler(request)

    def __eq__(self, other: 'Operation') -> bool:
        if isinstance(other, Operation):
            return all(
                getattr(self, a) == getattr(other, a)
                for a in ('path', 'methods')
            )
        return NotImplemented

    def __str__(self) -> str:
        return "{} - {} {}".format(self.operation_id, '|'.join(m for m in self.methods), self.path)

    def __repr__(self) -> str:
        return f"Operation({self.operation_id!r}, {self.path!r}, {self.methods})"

    def bind_to_instance(self, instance: object) -> None:
        """
        Bind a ResourceApi instance to an operation.
        """
        self.binding = instance
        self.middleware.append(instance)

    def op_paths(self, path_base: UrlPath.Atoms=None) -> Iterable[Tuple[UrlPath, 'Operation']]:
        """
        Return `URLPath`, `Operation` pairs.
        """
        url_path = self.path
        if path_base:
            url_path = path_base / url_path
        yield url_path, self

    @cached_property
    def path(self) -> UrlPath:
        return self._path

    @cached_property
    def is_bound(self) -> bool:
        """
        Operation is bound to a API Class
        """
        return bool(self.binding)

    # Docs ##########################################################

    def to_openapi(self) -> Dict[str, Any]:
        """
        Generate OpenAPI documentation
        """
        return dict_filter(
            operationId=self.operation_id,
        )

    @cached_property
    def operation_id(self) -> str:
        """
        Unique identifier of a specific operation
        """
        func = self.base_func
        value = getattr(func, 'operation_id', None)
        return value or f"{func.__module__}.{func.__name__}"

    @property
    def tags(self) -> Set[str]:
        """
        Tags associated with this operation
        """
        tags = set()
        if self._tags:
            tags.update(self._tags)
        if self.binding:
            binding_tags = getattr(self.binding, 'tags', None)
            if binding_tags:
                tags.update(binding_tags)
        return tags
