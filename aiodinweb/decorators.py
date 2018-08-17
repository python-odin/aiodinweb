from typing import Callable

from . import constants
from .data_structures import UrlPath, EmptyPath, Parameter
from .operation import Operation, OperationFunction, Methods


def operation(path: UrlPath.Atoms, **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Operation decorator, converts a function into an API operation.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner


def route(func: OperationFunction=None, *,
          path: UrlPath.Atoms=EmptyPath,
          **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Basic api route

    This applies defaults commonly associated with a listing of resources.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def listing(func: OperationFunction=None, *,
            path: UrlPath.Atoms=EmptyPath,
            **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Listing operation

    This applies defaults commonly associated with a listing of resources.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def create(func: OperationFunction=None, *,
           path: UrlPath.Atoms=EmptyPath,
           methods: Methods=constants.Method.Post,
           **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Create operation

    This applies defaults commonly associated with a creation of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def detail(func: OperationFunction=None, *,
           path: UrlPath.Atoms=UrlPath(Parameter('resource_id', constants.In.Path)),
           **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Detail operation

    This applies defaults commonly associated with getting the detail of a
    resource.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def update(func: OperationFunction, *,
           path: UrlPath.Atoms=UrlPath(Parameter('resource_id', constants.In.Path)),
           methods: Methods=constants.Method.Put,
           **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Update operation

    This applies defaults commonly associated with an update of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def patch(func: OperationFunction, *,
          path: UrlPath.Atoms=UrlPath(Parameter('resource_id', constants.In.Path)),
          methods: Methods=constants.Method.Patch,
          **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Patch operation

    This applies defaults commonly associated with patching a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def delete(func: OperationFunction, *,
           path: UrlPath.Atoms=UrlPath(Parameter('resource_id', constants.In.Path)),
           methods: Methods=constants.Method.Delete,
           **kwargs) -> Callable[[OperationFunction], Operation]:
    """
    Delete operation

    This applies defaults commonly associated with deletion of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner
