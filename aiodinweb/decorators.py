from typing import Callable, Union

from . import constants
from .data_structures import UrlPath, EmptyPath, Parameter
from .operation import Operation, OperationFunction, Methods


CollectionPath = EmptyPath
ResourcePath = UrlPath(Parameter('%(resource_key)s', constants.In.Path,
                                 data_type=constants.DataType.String))


OperationDecorator = Callable[[OperationFunction], Union[Operation, OperationFunction]]


def operation(path: UrlPath.Atoms, **kwargs) -> OperationDecorator:
    """
    Operation decorator, converts a function into an API operation.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner


def route(func: OperationFunction=None, *,
          path: UrlPath.Atoms=EmptyPath,
          **kwargs) -> OperationDecorator:
    """
    Basic api route

    This applies defaults commonly associated with a listing of resources.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def listing(func: OperationFunction=None, *,
            path: UrlPath.Atoms=CollectionPath,
            **kwargs) -> OperationDecorator:
    """
    Listing operation

    This applies defaults commonly associated with a listing of resources.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def create(func: OperationFunction=None, *,
           path: UrlPath.Atoms=CollectionPath,
           methods: Methods=constants.Method.Post,
           **kwargs) -> OperationDecorator:
    """
    Create operation

    This applies defaults commonly associated with a creation of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def detail(func: OperationFunction=None, *,
           path: UrlPath.Atoms=ResourcePath,
           **kwargs) -> OperationDecorator:
    """
    Detail operation

    This applies defaults commonly associated with getting the detail of a
    resource.
    """
    def inner(f: OperationFunction) -> Operation:
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def update(func: OperationFunction=None, *,
           path: UrlPath.Atoms=ResourcePath,
           methods: Methods=constants.Method.Put,
           **kwargs) -> OperationDecorator:
    """
    Update operation

    This applies defaults commonly associated with an update of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def patch(func: OperationFunction=None, *,
          path: UrlPath.Atoms=ResourcePath,
          methods: Methods=constants.Method.Patch,
          **kwargs) -> OperationDecorator:
    """
    Patch operation

    This applies defaults commonly associated with patching a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def delete(func: OperationFunction=None, *,
           path: UrlPath.Atoms=ResourcePath,
           methods: Methods=constants.Method.Delete,
           **kwargs) -> OperationDecorator:
    """
    Delete operation

    This applies defaults commonly associated with deletion of a resource.
    """
    def inner(f: OperationFunction) -> Operation:
        kwargs['methods'] = methods
        return Operation(f, path, **kwargs)
    return inner(func) if func else inner


def add_param(param: Parameter) -> OperationDecorator:
    """
    Add parameter to an operation.
    """
    def inner(f: OperationFunction) -> OperationFunction:
        try:
            getattr(f, 'parameters').add(param)
        except AttributeError:
            setattr(f, 'parameters', {param})
        return f
    return inner


def query_param(name: str, *,
                description: str=None,
                required: bool=None,
                allow_empty: bool=None,
                data_type: constants.DataType=constants.DataType.String) -> OperationDecorator:
    """
    Add a query param
    """
    return add_param(Parameter(name, constants.In.Query,
                               description=description,
                               required=required,
                               allow_empty=allow_empty,
                               data_type=data_type))


def header_param(name: str, *,
                 description: str=None,
                 required: bool=None,
                 allow_empty: bool=None,
                 data_type: constants.DataType=None) -> OperationDecorator:
    """
    Add a query param
    """
    return add_param(Parameter(name, constants.In.Header,
                               description=description,
                               required=required,
                               allow_empty=allow_empty,
                               data_type=data_type))


def cookie_param(name: str, *,
                 description: str=None,
                 required: bool=None,
                 allow_empty: bool=None,
                 data_type: constants.DataType=None) -> OperationDecorator:
    """
    Add a query param
    """
    return add_param(Parameter(name, constants.In.Cookie,
                               description=description,
                               required=required,
                               allow_empty=allow_empty,
                               data_type=data_type))


def deprecated(func: OperationFunction=None) -> OperationDecorator:
    """
    Mark an operation deprecated.
    """
    def inner(f: OperationFunction) -> OperationFunction:
        f.deprecated = True
        return f
    return inner(func) if operation else inner
