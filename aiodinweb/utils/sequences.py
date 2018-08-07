from typing import TypeVar, Tuple, List, Dict, Sequence, Union, Any

T = TypeVar('T')


def force_tuple(obj: Union[T, Iterable[T]]) -> Tuple[T]:
    """
    Force an incoming value to be a Tuple with special case for handling bytes
    and str values as single values rather than iterables.

    """
    if isinstance(obj, (str, bytes)):
        return obj,

    if isinstance(obj, tuple):
        return obj

    return tuple(obj)
