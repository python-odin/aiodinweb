import itertools

from typing import TypeVar, Tuple, Iterable, Union, Any

T = TypeVar('T')


def force_tuple(obj: Union[T, Iterable[T]]) -> Tuple[T]:
    """
    Force an incoming value to be a Tuple with special case for handling bytes
    and str values as single values rather than iterable.

    """
    if isinstance(obj, (str, bytes)):
        return obj,

    if isinstance(obj, tuple):
        return obj

    if isinstance(obj, Iterable):
        return tuple(obj)

    return obj,


def dict_filter_update(base: dict, updates: dict) -> None:
    """
    Update dict with None values filtered out.
    """
    base.update((k, v) for k, v in updates.items() if v is not None)


def dict_filter(*args: dict, **kwargs: Any) -> dict:
    """
    Merge all values into a single dict with all None values removed.
    """
    result = {}
    for arg in itertools.chain(args, (kwargs,)):
        dict_filter_update(result, arg)
    return result
